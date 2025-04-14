from scrapy.spiders import SitemapSpider

# from products.categories import PaymentMethods, map_payment
from products.structured_data_spider import StructuredDataSpider


class JokerNOSpider(SitemapSpider, StructuredDataSpider):
    name = "joker_no"
    allowed_domains = ["joker.no"]

    sitemap_urls = ["https://joker.no/robots.txt"]
    sitemap_rules = [
        (r"https://joker.no/nettbutikk/[\w-]+/[\w-]+/[\w-]+/[\w-]+-[\d]+", "parse_sd"),
    ]