from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class SeijoishiiJPSpider(SitemapSpider, StructuredDataSpider):
    name = "seijoishii_jp"
    allowed_domains = ["seijoishii.com"]

    sitemap_urls = ["https://seijoishii.com/robots.txt"]
    sitemap_rules = [
        (r"https://seijoishii.com/products/\d+", "parse_sd"),
    ]
