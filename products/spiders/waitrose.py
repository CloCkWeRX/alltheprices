from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class WaitroseSpider(SitemapSpider, StructuredDataSpider):
    name = "waitrose"
    allowed_domains = ["waitrose.com"]
    sitemap_urls = ["https://www.waitrose.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.waitrose.com/ecom/products/[\w-]+/[\w-]+", "parse_sd"),
    ]
