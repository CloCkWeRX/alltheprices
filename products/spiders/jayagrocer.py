from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class JayagrocerSpider(SitemapSpider, StructuredDataSpider):
    name = "jayagrocer"
    allowed_domains = ["jayagrocer.com"]

    sitemap_urls = ["https://jayagrocer.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://jayagrocer.com/products/[\w-]+", "parse_sd"),
    ]
