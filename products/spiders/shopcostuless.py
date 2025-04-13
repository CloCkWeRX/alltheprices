from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class ShopcostulessSpider(SitemapSpider, StructuredDataSpider):
    name = "shopcostuless"
    allowed_domains = ["shopcostuless.com"]

    sitemap_urls = ["https://shopcostuless.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.shopcostuless.com/shop/[\w-]+/(.*)", "parse_sd"),
    ]
