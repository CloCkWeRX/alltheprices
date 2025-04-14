from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class VarusUASpider(SitemapSpider, StructuredDataSpider):
    name = "varus_ua"
    allowed_domains = ["varus.ua"]

    sitemap_urls = ["https://varus.ua/robots.txt"]
    sitemap_rules = [
        # Filter for at least two hyphens, to skip top level non product pages
        (r"https://varus.ua/[\w]+-[\w]+-[\w-]+", "parse_sd"),
    ]
