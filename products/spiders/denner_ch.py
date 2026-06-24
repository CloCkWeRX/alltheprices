from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class DennerCHSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Denner (Switzerland).
    Wikidata: Q379911

    Sample output structured data:
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "brand": {
            "@type": "Brand",
            "name": "Denner"
        },
        "sku": "463348",
        "mpn": "463348",
        "name": "Winston Hundefutter Kalb mit frischem Pansen",
        "image": [
            "https://denner.imgix.net/assets/c2b834da-919f-4352-af6d-ee657caa825b/web/463348_24_01_15.png"
        ],
        "description": "ohne Zucker- und Getreidezusatz, 175 g",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://www.denner.ch/de/aktionen/~p463348?locale=de&context=default",
                "availability": "https://schema.org/InStoreOnly",
                "price": 1.4,
                "priceCurrency": "CHF"
            }
        ]
    }
    """

    name = "denner_ch"
    allowed_domains = ["denner.ch"]
    user_agent = BROWSER_DEFAULT

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q379911",
                "name": "Denner",
            }
        }
    }

    sitemap_urls = ["https://www.denner.ch/sitemap.xml"]
    sitemap_rules = [
        (r"~p(\d+)(?:\?.*)?$", "parse"),
    ]
