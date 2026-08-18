import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ColesAUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Coles Supermarkets (Australia).
    Wikidata: Q1108172
    Fixes #476.
    """

    name = "coles_au"
    allowed_domains = ["coles.com.au"]
    sitemap_urls = ["https://www.coles.com.au/sitemap/sitemap-index-products.xml"]
    sitemap_rules = [(r"/product/.*-(\d+)$", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.5,
    }

    item_attributes = {
        "located_in_wikidata": "Q1108172",
    }

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                product = data.get("props", {}).get("pageProps", {}).get("product")
                if product:
                    pricing = product.get("pricing") or {}
                    price = pricing.get("now")

                    images = product.get("imageUris") or []
                    image_url = None
                    if images and isinstance(images, list):
                        uri = images[0].get("uri")
                        if uri:
                            if uri.startswith("http"):
                                image_url = uri
                            else:
                                assets_url = data.get("props", {}).get("pageProps", {}).get("assetsUrl") or "https://cdn.productimages.coles.com.au/productimages"
                                image_url = f"{assets_url.rstrip('/')}{uri}"

                    brand = product.get("brand")
                    if brand:
                        brand_obj = {"@type": "Brand", "name": brand}
                    else:
                        brand_obj = None

                    sku = str(product.get("id")) if product.get("id") else None

                    name = product.get("name")
                    size = product.get("size")
                    if name and size and size not in name:
                        full_name = f"{brand + ' ' if brand and brand not in name else ''}{name} {size}".strip()
                    elif name:
                        full_name = f"{brand + ' ' if brand and brand not in name else ''}{name}".strip()
                    else:
                        full_name = None

                    ld_item = {
                        "@type": "Product",
                        "name": full_name or name,
                        "brand": brand_obj,
                        "sku": sku,
                        "image": image_url,
                        "description": product.get("description"),
                        "offers": {
                            "@type": "Offer",
                            "price": price,
                            "priceCurrency": "AUD",
                            "availability": "https://schema.org/InStock",
                            "url": response.url,
                        },
                    }
                    yield ld_item
                    return
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        yield from super().iter_linked_data(response)

    def post_process_item(self, item: Product, response: Response, ld_data: dict):
        if not item.get("ref"):
            item["ref"] = self.get_ref(response.url, response)
        if not item.get("proof_currency"):
            item["proof_currency"] = "AUD"
        yield item

    def get_ref(self, url: str, response: Response = None) -> str:
        match = re.search(r"/product/.*-(\d+)$", url)
        if match:
            return match.group(1)
        return super().get_ref(url, response)
