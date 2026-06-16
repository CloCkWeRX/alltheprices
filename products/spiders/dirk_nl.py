from products.linked_data_parser import LinkedDataParser
from products.structured_data_spider import StructuredDataSpider
from scrapy.spiders import SitemapSpider


class DirkNLSpider(SitemapSpider, StructuredDataSpider):
    name = "dirk_nl"
    allowed_domains = ["dirk.nl"]
    sitemap_urls = ["https://www.dirk.nl/sitemap.xml"]
    sitemap_rules = [
        (r"/boodschappen/.*/(\d+)", "parse_sd"),
        (r"/boodschappen/", "parse_sd"),
    ]

    def iter_linked_data(self, response):
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("@type") == "ItemList":
                for element in ld_obj.get("itemListElement", []):
                    item = element.get("item")
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        yield item

        yield from super().iter_linked_data(response)

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q17502722",
                "name": "Dirk",
            }
        }
    }

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": 120,
    }
