from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class GiantTigerSpider(SitemapSpider, StructuredDataSpider):
    name = "giant_tiger"
    allowed_domains = ["gianttiger.com"]

    sitemap_urls = ["https://www.gianttiger.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.gianttiger.com/products/.*", "parse_sd"),
    ]
