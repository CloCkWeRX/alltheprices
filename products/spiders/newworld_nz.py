from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class NewworldNZSpider(SitemapSpider, StructuredDataSpider):
    name = "newworld_nz"
    allowed_domains = ["newworld.co.nz"]
    sitemap_urls = ["https://www.newworld.co.nz/robots.txt"]
    sitemap_rules = [
        (r"shop/product/[\d\w_]+", "parse_sd"),
    ]
