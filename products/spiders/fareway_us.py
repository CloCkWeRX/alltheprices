from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class FarewayUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Fareway (United States).
    Wikidata: Q5434998
    Fix #462.
    """
    name = "fareway_us"
    allowed_domains = ["shop.fareway.com"]
    sitemap_urls = ["https://shop.fareway.com/sitemaps/storefront_pro/shop_fareway_com/sitemap.xml"]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q5434998",
        "brand_wikidata": "Q5434998",
        "proof_currency": "USD",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5434998",
                "name": "Fareway",
            }
        }
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            # We only want to crawl product sitemaps
            if "products" in entry["loc"]:
                yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Enforce currency is USD
        item["proof_currency"] = "USD"
        item["located_in_wikidata"] = "Q5434998"
        yield item
