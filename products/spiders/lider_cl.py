from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LiderCLSpider(SitemapSpider, StructuredDataSpider):
    name = "lider_cl"
    allowed_domains = ["lider.cl"]
    sitemap_urls = ["https://www.lider.cl/siteindex.xml"]
    sitemap_rules = [
        (r"/ip/.*/(\d+)$", "parse_sd"),
    ]

    item_attributes = {
        "brand": "Líder",
        "brand_wikidata": "Q6711261",
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }
