from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class CombiDESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Combi (Germany).

    Sample output:
    {
        'extras': {
            'seller': {
                '@type': 'Organization',
                '@id': 'https://www.wikidata.org/wiki/Q1113618',
                'name': 'Combi'
            }
        },
        'image': 'https://d2y99t05v0nd2u.cloudfront.net/products/images/4507010015_2099990155232.jpg.jpg',
        'name': 'Lauchzwiebeln im Bund',
        'offers': [{
            '@type': 'Offer',
            'availability': 'https://schema.org/InStock',
            'itemCondition': 'https://schema.org/NewCondition',
            'priceSpecification': {
                '@type': 'UnitPriceSpecification',
                'price': '1.29',
                'priceCurrency': 'EUR',
                'valueAddedTaxIncluded': True
            }
        }],
        'ref': '4507010015',
        'website': 'https://www.combi.de/lauchzwiebeln_im_bund_4507010015.html'
    }
    """

    name = "combi_de"
    allowed_domains = ["combi.de"]
    user_agent = BROWSER_DEFAULT

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
        (r"/.*_(\d+)\.html$", "parse_sd"),
    ]
