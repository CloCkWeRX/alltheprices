from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class OkayBESpider(SitemapSpider, StructuredDataSpider):
    """
    OKay (Belgium) spider.
    Fixes #454.
    Wikidata: Q2159701
    Parent: Colruyt Group (Q1111963)

    Sample output:
    {
        "name": "Graisse pr friture végétale",
        "website": "https://www.okay.be/fr/produits/13732",
        "image": "https://static.colruytgroup.com/images/500x500/std.lang.all/21/52/asset-382152.jpg",
        "ref": "13732",
        "brand": "Solo",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2159701",
                "name": "OKay",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q1111963",
                    "name": "Colruyt Group"
                }
            }
        }
    }
    """

    name = "okay_be"
    allowed_domains = ["okay.be"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2159701",
                "name": "OKay",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q1111963",
                    "name": "Colruyt Group",
                },
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    sitemap_urls = [
        "https://www.okay.be/nl/sitemap.products.xml",
        "https://www.okay.be/fr/sitemap.products.xml",
    ]
    sitemap_rules = [
        (r"/(?:produits|producten)/(\d+)$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        brand_data = ld_data.get("brand")
        if brand_data:
            if isinstance(brand_data, dict):
                item["brand"] = brand_data.get("name")
            elif isinstance(brand_data, str):
                item["brand"] = brand_data
        yield item
