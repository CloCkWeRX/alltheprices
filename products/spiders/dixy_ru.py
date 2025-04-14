from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class DixyRUSpider(SitemapSpider, StructuredDataSpider):
    name = "dixy_ru"
    allowed_domains = ["dixy.ru"]

    sitemap_urls = ["https://dixy.ru/sitemap.xml"]
    sitemap_rules = [
        (r"https://dixy.ru/catalog/[\w-]+/[\w-]+/[\d]+/", "parse_sd"),
    ]
