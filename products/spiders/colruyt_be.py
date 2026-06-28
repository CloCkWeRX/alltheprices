from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ColruytBESpider(SitemapSpider, StructuredDataSpider):
    """
    Colruyt (Belgium) spider.
    Fixes #117.
    Wikidata: Q2363991
    Parent: Colruyt Group (Q1111963)

    Sample output:
    {
        "name": "Bio graines de courge",
        "website": "https://www.colruyt.be/fr/produits/22932",
        "image": "https://static.colruytgroup.com/images/500x500/std.lang.all/07/70/asset-3990770.jpg",
        "ref": "22932",
        "brand": "Econoce",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2363991",
                "name": "Colruyt",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q1111963",
                    "name": "Colruyt Group"
                }
            }
        }
    }
    """

    name = "colruyt_be"
    allowed_domains = ["colruyt.be"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2363991",
                "name": "Colruyt",
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
        "https://www.colruyt.be/nl/sitemap.products.xml",
        "https://www.colruyt.be/fr/sitemap.products.xml",
    ]
    sitemap_rules = [
        (r"/(?:produits|producten)/(\d+)$", "parse_sd"),
    ]
