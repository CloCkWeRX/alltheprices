from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class NabijiGESpider(SitemapSpider, StructuredDataSpider):
    name = "2nabiji_ge"
    allowed_domains = ["2nabiji.ge"]

    sitemap_urls = ["https://2nabiji.ge/robots.txt"]
    sitemap_rules = [
        (r"https://2nabiji.ge/ge/product/[\w-]+", "parse_sd"),
    ]

    # TODO: Post process item to get prices
