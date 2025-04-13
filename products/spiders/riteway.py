from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class RitewaySpider(SitemapSpider, StructuredDataSpider):
    name = "riteway"
    allowed_domains = ["riteway.vg"]

    sitemap_urls = ["https://www.riteway.vg/robots.txt"]
    sitemap_rules = [
        (r"https://www.riteway.vg/[\w-]+", "parse_sd"),
    ]
