from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class OnurmarketSpider(SitemapSpider, StructuredDataSpider):
    name = "onurmarket"
    allowed_domains = ["onurmarket.com"]

    sitemap_urls = ["https://www.onurmarket.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.onurmarket.com/[\w-]+", "parse_sd"),
    ]
