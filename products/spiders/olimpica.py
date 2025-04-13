from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class OlimpicaSpider(SitemapSpider, StructuredDataSpider):
    name = "olimpica"
    allowed_domains = ["olimpica.com"]

    sitemap_urls = ["https://www.olimpica.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.olimpica.com/[\w-]+/p", "parse_sd"),
    ]
