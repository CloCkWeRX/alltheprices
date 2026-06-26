from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class BioplanetBESpider(SitemapSpider, StructuredDataSpider):
    """
    Bio-Planet (Belgium) spider.
    Fixes #107.
    Wikidata: Q122415968
    Parent: Colruyt Group (Q1111963)

    Sample output:
    {
        "name": "Sesampasta Bio",
        "website": "https://www.bioplanet.be/nl/producten/bio-elstar-appelen-circa-1kg-8212",
        "image": "https://static.colruytgroup.com/images/500x500/std.lang.all/89/90/asset-368990.jpg",
        "ref": "8212",
        "brand": "Oxfam fairtrade",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q122415968",
                "name": "Bio-Planet",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q1111963",
                    "name": "Colruyt Group"
                }
            }
        }
    }
    """

    name = "bioplanet_be"
    allowed_domains = ["bioplanet.be"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q122415968",
                "name": "Bio-Planet",
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

    sitemap_urls = ["https://www.bioplanet.be/nl/sitemap.products.xml"]
    sitemap_rules = [
        (r"/producten/(?:.*-)?(\d+)$", "parse_sd"),
    ]
