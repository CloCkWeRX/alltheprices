from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class OdinNLSpider(SitemapSpider, StructuredDataSpider):
    name = "odin_nl"
    allowed_domains = ["odin.nl"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q114839627",
                "name": "Coöperatie Odin",
            }
        }
    }

    sitemap_urls = ["https://www.odin.nl/robots.txt"]
    sitemap_rules = [
        # https://www.hmart.com/tempura-udon-cup-noodle-cup-2-6oz-75g--6-cups/p
        (r"https://www.odin.nl/producten/alle-producten/[\w-]+/", "parse_sd"),
    ]
