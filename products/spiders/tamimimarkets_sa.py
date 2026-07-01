import json
import re
from typing import Iterable

from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class TamimimarketsSASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Tamimi Markets (Saudi Arabia).
    Issue #319. Wikidata Q7681456.

    Sample output:
    {
        "brand": "Halah",
        "brand_wikidata": "Q7681456",
        "gtin": "6281011138799",
        "image": "https://storage.googleapis.com/tm-zopsmart-uploads/320/20201101/368556_1-20201101-005836.png",
        "name": "Pure Sunflower Oil-1.5 L",
        "offers": [
            {
                "@type": "Offer",
                "price": 18.25,
                "priceCurrency": "SAR"
            }
        ],
        "ref": "217160",
        "website": "https://shop.tamimimarkets.com/product/pure-sunflower-oil-7"
    }
    """

    name = "tamimimarkets_sa"
    allowed_domains = ["shop.tamimimarkets.com"]
    sitemap_urls = ["https://shop.tamimimarkets.com/sitemaps/product1.xml"]
    sitemap_rules = [(r"/product/", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "brand_wikidata": "Q7681456",
    }

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Tamimi Markets embeds data in __NEXT_DATA__ script tag.
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                entity = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("data", {})
                    .get("page", {})
                    .get("entity", {})
                )
                if entity:
                    brand_name = entity.get("brand", {}).get("name")
                    for variant in entity.get("variants", []):
                        # Construct a Schema.org-like object for StructuredDataSpider to parse
                        ld_item = {
                            "@type": "Product",
                            "name": variant.get("fullName") or entity.get("name"),
                            "brand": brand_name,
                            "sku": str(variant.get("id")),
                            "image": variant.get("images")[0] if variant.get("images") else None,
                        }

                        if variant.get("barcodes"):
                            ld_item["gtin"] = variant["barcodes"][0]

                        offers = []
                        for store_data in variant.get("storeSpecificData", []):
                            # We'll take the first store's price as representative if multiple exist
                            if store_data.get("mrp"):
                                offers.append(
                                    {
                                        "@type": "Offer",
                                        "price": float(store_data["mrp"]),
                                        "priceCurrency": "SAR",
                                    }
                                )

                        if offers:
                            ld_item["offers"] = offers

                        yield ld_item
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        yield from super().iter_linked_data(response)

    def post_process_item(self, item: Product, response, ld_data):
        # Ensure ref is the SKU/variant ID
        if ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        yield item
