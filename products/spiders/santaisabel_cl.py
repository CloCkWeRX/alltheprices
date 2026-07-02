import codecs
import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SantaisabelCLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Santa Isabel (Chile).
    Extracts product data from window.__renderData in HTML.

    Sample output:
    {
        "brand_wikidata": "Q7419614",
        "extras": {
            "@source_uri": "https://www.santaisabel.cl/bebida-coca-cola-light-3-l/p",
            "owner": {
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "@type": "Organization",
                "name": "Cencosud"
            }
        },
        "image": "https://santaisabel.vtexassets.com/arquivos/ids/210131/Bebida-Coca-Cola-light-3-L.jpg?v=637979920913200000",
        "name": "Bebida Coca-Cola Light 3 L",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
                "price": 2550,
                "priceCurrency": "CLP",
                "seller": {
                    "@type": "Organization",
                    "name": "santaisabel"
                }
            }
        ],
        "ref": "72",
        "website": "https://www.santaisabel.cl/bebida-coca-cola-light-3-l/p"
    }
    """

    name = "santaisabel_cl"
    allowed_domains = ["santaisabel.cl", "supabase.co"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.santaisabel.cl/sitemap.xml"]
    sitemap_follow = ["santaisabel-custom"]
    sitemap_rules = [
        (r"/p$", "parse_sd"),
    ]

    item_attributes = {
        "brand_wikidata": "Q7419614",
        "extras": {
            "owner": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "name": "Cencosud",
            }
        },
    }

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # Santa Isabel uses window.__renderData to store product information.
        # It's a JSON string within the HTML.
        # Use regex to find it, handling potential escaping.
        render_data_match = re.search(r"window\.__renderData\s*=\s*\"(.*)\"\s*;", response.text)
        if not render_data_match:
            # Fallback if the semicolon is missing or there's other variation
            render_data_match = re.search(r"window\.__renderData\s*=\s*\"(.*)\"", response.text)

        if not render_data_match:
            return

        try:
            raw_data = render_data_match.group(1)
            # The data is double-escaped. We can use codecs.decode to unescape it.
            decoded_data = codecs.decode(raw_data, "unicode_escape")
            data = json.loads(decoded_data)

            pdp_product = data.get("pdp", {}).get("product", [])
            for prod in pdp_product:
                brand_name = prod.get("brand")
                product_name = prod.get("productName")
                description = prod.get("description")

                for item in prod.get("items", []):
                    offers = []
                    images = [img.get("imageUrl") for img in item.get("images", [])]

                    for seller in item.get("sellers", []):
                        comm_offer = seller.get("commertialOffer", {})
                        price = comm_offer.get("Price")
                        availability = (
                            "https://schema.org/InStock"
                            if comm_offer.get("AvailableQuantity", 0) > 0
                            else "https://schema.org/OutOfStock"
                        )

                        offers.append(
                            {
                                "@type": "Offer",
                                "price": price,
                                "priceCurrency": "CLP",
                                "availability": availability,
                                "itemCondition": "https://schema.org/NewCondition",
                                "seller": {
                                    "@type": "Organization",
                                    "name": seller.get("sellerName"),
                                },
                            }
                        )

                    yield {
                        "@context": "http://schema.org/",
                        "@type": "Product",
                        "name": product_name,
                        "brand": {"@type": "Brand", "name": brand_name},
                        "description": description,
                        "image": images[0] if images else None,
                        "sku": item.get("itemId"),
                        "gtin": item.get("ean"),
                        "offers": offers,
                        "url": response.url,
                    }

        except Exception as e:
            self.logger.error(f"Error parsing window.__renderData on {response.url}: {e}")

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        if not item.get("ref") and ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        yield item
