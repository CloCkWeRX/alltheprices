from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class ChedrauiComMXSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Chedraui (Mexico).
    Wikidata: Q2961952

    Sample output structured data:
    {
        "name": "Avena Bob's Red Mill Orgánica Estilo Escocés 567g",
        "website": "https://www.chedraui.com.mx/avena-bobs-red-mill-organica-estilo-escoces-567g-3344281/p",
        "image": "https://chedrauimx.vtexassets.com/arquivos/ids/70006182/39978029560_00.jpg?v=639150049591370000",
        "ref": "03344281",
        "offers": [
            {
                "@type": "AggregateOffer",
                "lowPrice": 229,
                "highPrice": 229,
                "priceCurrency": "MXN",
                "offers": [
                    {
                        "@type": "Offer",
                        "price": 229,
                        "priceCurrency": "MXN",
                        "availability": "http://schema.org/InStock",
                        "sku": "03344281",
                        "itemCondition": "http://schema.org/NewCondition",
                        "priceValidUntil": "2027-06-19T00:00:00Z",
                        "seller": {
                            "@type": "Organization",
                            "name": "Chedraui"
                        }
                    }
                ],
                "offerCount": 1
            }
        ]
    }
    """

    name = "chedraui_com_mx"
    allowed_domains = ["chedraui.com.mx"]
    user_agent = BROWSER_DEFAULT

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2961952",
                "name": "Chedraui",
            }
        }
    }

    sitemap_urls = ["https://www.chedraui.com.mx/sitemap.xml"]
    sitemap_rules = [
        (r"/.*-(\d+)/p$", "parse_sd"),
    ]
