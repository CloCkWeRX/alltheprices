from scrapy.spiders import SitemapSpider

# from products.categories import PaymentMethods, map_payment
from products.structured_data_spider import StructuredDataSpider


class JokerNOSpider(SitemapSpider, StructuredDataSpider):
    name = "joker_no"
    allowed_domains = ["joker.no"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q716328",
                "name": "Joker",
            }
        }
    }

    sitemap_urls = ["https://joker.no/robots.txt"]
    sitemap_rules = [
        (r"https://joker.no/nettbutikk/[\w-]+/[\w-]+/[\w-]+/[\w-]+-[\d]+", "parse_sd"),
    ]
