from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CombiDESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Combi (Germany).
    Sample output:
    {
        'extras': {
            'seller': {
                '@id': 'https://www.wikidata.org/wiki/Q1113618',
                '@type': 'Organization',
                'name': 'Combi'
            }
        },
        'image': 'https://d2y99t05v0nd2u.cloudfront.net/products/images/4503060174_4000521579203_01.jpg',
        'name': 'Dr. Oetker Crème fraîche classic',
        'offers': [
            {
                '@type': 'Offer',
                'availability': 'https://schema.org/InStock',
                'itemCondition': 'https://schema.org/NewCondition',
                'priceSpecification': {
                    '@type': 'UnitPriceSpecification',
                    'price': '2.69',
                    'priceCurrency': 'EUR',
                    'valueAddedTaxIncluded': True
                }
            }
        ],
        'ref': '4503060174',
        'website': 'https://www.combi.de/dr._oetker_cr%c3%a8me_fra%c3%aeche_classic_4503060174.html'
    }
    """

    name = "combi_de"
    allowed_domains = ["combi.de"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1113618",
                "name": "Combi",
            }
        }
    }

    sitemap_urls = ["https://www.combi.de/sitemaps/combi/sitemap.produkte.xml"]
    sitemap_rules = [
        (r"_(\d+)\.html$", "parse_sd"),
    ]
