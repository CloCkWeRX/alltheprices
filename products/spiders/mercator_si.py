import json
import re
from typing import Iterable

from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider


class MercatorSISpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Mercator (Slovenia).
    Extracts product data from the `analyticsObject` JavaScript variable as the site lacks standard Schema.org JSON-LD.

    Sample output:
    {
        "name": "Margarina, Zvijezda, 250 g",
        "website": "https://mercatoronline.si/izdelek/22419/margarina-zvijezda-250-g",
        "image": "https://mercatoronline.si/img/cache/products/4909/product_medium_image/00000040.jpg",
        "ref": "22419",
        "brand": "ZVIJEZDA",
        "located_in_wikidata": "Q1366974",
        "price": 1.09,
        "proof_currency": "EUR",
        "offers": [
            {
                "@type": "Offer",
                "price": 1.09,
                "priceCurrency": "EUR"
            }
        ],
        "extras": {}
    }
    """

    name = "mercator_si"
    allowed_domains = ["mercatoronline.si"]
    sitemap_urls = ["https://mercatoronline.si/sitemap.xml"]
    sitemap_rules = [(r"/izdelek/(\d+)/", "parse_sd")]

    def iter_linked_data(self, response) -> Iterable[dict]:
        # The site does not provide standard Schema.org JSON-LD in static HTML.
        # We extract product data from the analyticsObject variable used for GA4.
        match = re.search(r"var analyticsObject = (\{.*?});", response.text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                items = data.get("ecommerce", {}).get("items", [])
                if items:
                    product_data = items[0]
                    yield {
                        "@context": "https://schema.org",
                        "@type": "Product",
                        "name": product_data.get("item_name"),
                        "sku": str(product_data.get("item_id")),
                        "brand": {"@type": "Brand", "name": product_data.get("item_brand")},
                        "offers": {
                            "@type": "Offer",
                            "price": product_data.get("price"),
                            "priceCurrency": product_data.get("currency", "EUR"),
                        },
                    }
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse analyticsObject JSON")

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q1366974"
        item["proof_currency"] = "EUR"
        yield item
