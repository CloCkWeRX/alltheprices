from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class CovabraBRSpider(SitemapSpider, StructuredDataSpider):
    name = "covabra_br"
    allowed_domains = ["covabra.com.br"]
    user_agent = BROWSER_DEFAULT

    sitemap_urls = ["https://www.covabra.com.br/sitemap.xml"]
    sitemap_rules = [
        (r"/p$", "parse_sd"),
    ]

    item_attributes = {
        "brand_wikidata": "Q131063998",
        "extras": {
            "seller": {
                "@type": "Organization",
                "name": "Covabra",
                "@id": "https://www.wikidata.org/wiki/Q131063998",
            }
        },
    }

    def post_process_item(self, item: Product, response: Response, ld_data: dict):
        if not item.get("ref"):
            # Try to get ref from sku or mpn if missing
            item["ref"] = item.get("sku") or item.get("mpn")

        if item.get("name"):
            yield item
