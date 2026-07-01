from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LottemartzettaKRSpider(SitemapSpider, StructuredDataSpider):
    """
    Lotte Mart Zetta (South Korea) spider.
    Fixes #274.
    Wikidata: Q326715 (Lotte Mart)
    """

    name = "lottemartzetta_kr"
    allowed_domains = ["lottemartzetta.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q326715",
                "name": "Lotte Mart",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://lottemartzetta.com/sitemaps/sitemap_index.xml",
    ]
    sitemap_rules = [
        (r"/products/(OS[A-Z0-9]+)/details", "parse_sd"),
    ]

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            if "products" in request.url:
                request.meta["playwright"] = True
            yield request
