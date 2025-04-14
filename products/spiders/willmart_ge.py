from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class WillmartGESpider(SitemapSpider, StructuredDataSpider):
    name = "willmart_ge"
    allowed_domains = ["willmart.ge"]

    sitemap_urls = ["https://willmart.ge/robots.txt"]
    sitemap_rules = [
        (r"https://willmart.ge/shop/[\w-]+/[\w-]+", "parse_sd"),
    ]
