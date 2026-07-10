from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider


class EblnaturkostDESpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for ebl-naturkost (Germany).
    Fixes #129.
    Wikidata: Q22691722

    Sample output:
    {
        "name": "Deutsche Bunte Karotten",
        "website": "https://www.ebl-naturkost.de/deutsche-bunte-karotten/004835",
        "ref": "004835",
        "image": "https://www.ebl-naturkost.de/media/b9/fc/31/1642413349/bunte-moehren_mueller-oelbke_004835_2022_w.png?1642413351",
        "located_in_wikidata": "Q22691722",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/SoldOut",
                "itemCondition": "https://schema.org/NewCondition",
                "priceCurrency": "EUR",
                "priceValidUntil": "2026-07-10",
                "url": "https://www.ebl-naturkost.de/deutsche-bunte-karotten/004835",
                "price": 1.97
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q22691722",
                "name": "ebl-naturkost"
            }
        }
    }
    """

    name = "eblnaturkost_de"
    allowed_domains = ["ebl-naturkost.de"]
    start_urls = [
        "https://www.ebl-naturkost.de/angebote/aktuelle-ebl-wochen-angebote/",
        "https://www.ebl-naturkost.de/angebote/natuerlich-rein-monats-angebote/",
    ]

    rules = (
        Rule(
            LinkExtractor(
                allow=(r"/[^/]+/\d{4,6}$",),
            ),
            callback="parse_sd",
        ),
        Rule(
            LinkExtractor(
                allow=(r"/angebote/",),
            ),
            follow=True,
        ),
    )

    item_attributes = {
        "located_in_wikidata": "Q22691722",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q22691722",
                "name": "ebl-naturkost",
            }
        },
    }
