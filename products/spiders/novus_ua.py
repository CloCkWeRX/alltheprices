from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class NovusUASpider(SitemapSpider, StructuredDataSpider):
    name = "novus_ua"
    allowed_domains = ["novus.ua"]

    sitemap_urls = ["https://novus.ua/sitemap.xml"]
    sitemap_rules = [
        (r"https://novus.ua/[\w-]+.html", "parse_sd"),
    ]
