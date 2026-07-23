import json
import re
from typing import Iterable
from urllib.parse import urlparse

from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ForaUASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Fora (Ukraine).
    Wikidata: Q4491805
    """

    name = "fora_ua"
    allowed_domains = ["fora.ua", "api.catalog.ecom.fora.ua"]
    user_agent = FIREFOX_LATEST
    convert_microdata = False  # Avoid JSON-LD microdata extraction error on raw API JSON response

    sitemap_urls = ["https://fora.ua/sitemap.xml"]
    sitemap_rules = [
        (r"/product/.*-(\d+)$", "parse_product_page"),
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            # We want to filter sitemap links to avoid crawling non-product sitemaps
            if "sitemap-products" in entry["loc"] or "product" in entry["loc"]:
                yield entry

    def parse_product_page(self, response):
        # We parse the URL slug
        parsed_url = urlparse(response.url)
        path = parsed_url.path
        # Extract slug
        slug = path.split("/")[-1]

        # Trigger a JSON POST request to the EcomCatalogGlobal API
        payload = {
            "method": "GetDetailedCatalogItem",
            "data": {
                "deliveryType": 2,
                "filialId": 310,
                "slug": slug,
                "merchantId": 2,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Referer": response.url,
        }

        yield Request(
            url="https://api.catalog.ecom.fora.ua/api/2.0/exec/EcomCatalogGlobal",
            method="POST",
            body=json.dumps(payload),
            headers=headers,
            callback=self.parse_api_response,  # Custom parse callback to completely bypass StructuredDataSpider's HTML/canonical methods
            meta={"original_url": response.url},
        )

    def parse_api_response(self, response):
        # Parse JSON API response
        try:
            data = json.loads(response.text)
        except Exception:
            return

        item_data = data.get("item")
        if not item_data:
            return

        name = item_data.get("name")
        sku = item_data.get("id")
        price = item_data.get("price")
        old_price = item_data.get("oldPrice")

        image = item_data.get("mainImage")
        if not image and item_data.get("images"):
            image = item_data["images"][0].get("path")

        description = item_data.get("weightPackedItemNote")

        # Map to Schema.org dict
        ld_obj = {
            "@type": "Product",
            "name": name,
            "sku": sku,
            "image": image,
            "description": description,
            "offers": {
                "@type": "Offer",
                "price": price,
                "priceCurrency": "UAH",
                "price_is_discounted": old_price is not None,
                "price_without_discount": old_price,
            },
        }

        # Extract brand/trademark
        parameters = item_data.get("parameters", [])
        brand = None
        for p in parameters:
            if p.get("key") == "trademark":
                brand = p.get("value")
                break
        if brand:
            ld_obj["brand"] = brand

        # We construct and yield the Product item directly
        item = Product()
        item["name"] = name
        item["image"] = image
        item["ref"] = str(sku) if sku else None
        item["website"] = response.meta.get("original_url")
        item["description"] = description
        if brand:
            item["brand"] = brand

        item["price"] = price
        item["proof_currency"] = "UAH"
        item["price_is_discounted"] = old_price is not None
        item["price_without_discount"] = old_price
        item["located_in_wikidata"] = "Q4491805"

        yield item
