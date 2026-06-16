from scrapy.spiders import SitemapSpider
from scrapy.linkextractors import LinkExtractor

from products.structured_data_spider import StructuredDataSpider


class CoopFirenzeSpider(SitemapSpider, StructuredDataSpider):
    name = "coopfirenze_it"
    allowed_domains = ["prenotalaspesa.coopfirenze.it"]
    sitemap_urls = ["https://prenotalaspesa.coopfirenze.it/robots.txt"]
    sitemap_rules = [
        (r"/[0-9]{13}\.html", "parse_sd"),
        (r"/", "parse_category"),
    ]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4004707",
                "name": "Unicoop Firenze",
            }
        }
    }

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": 120,
    }

    product_extractor = LinkExtractor(
        allow=r"/[0-9]{13}\.html",
    )

    def parse_category(self, response):
        for link in self.product_extractor.extract_links(response):
            yield response.follow(link, callback=self.parse_sd)
