from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class BotanicFRSpider(SitemapSpider, StructuredDataSpider):
    name = "botanic_fr"
    allowed_domains = ["botanic.com"]

    sitemap_urls = ["https://www.botanic.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.botanic.com/produit/\d+/[\w]+.html", "parse_sd"),
    ]
