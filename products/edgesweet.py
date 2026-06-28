from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class EdgesweetSpider(SitemapSpider, StructuredDataSpider):
    """
    Base spider for Edgesweet sites (Kroger subsidiaries).
    Product pages are typically identified by /p/(slug)/id
    """

    sitemap_rules = [
        (r"/p/(.*)/\d+", "parse_sd"),
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }
