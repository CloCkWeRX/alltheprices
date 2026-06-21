from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider

class LidlBGSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Lidl Bulgaria (lidl.bg)

    Sample output:
    {
        'extras': {
            'seller': {
                '@type': 'Organization',
                '@id': 'https://www.wikidata.org/wiki/Q108169047',
                'name': 'Lidl Bulgaria',
                'parentOrganization': {
                    '@type': 'Organization',
                    '@id': 'https://www.wikidata.org/wiki/Q151954',
                    'name': 'Lidl'
                }
            }
        },
        'name': 'Кроасани',
        'website': 'https://www.lidl.bg/p/italiamo-kroasani/p10058789',
        'image': 'https://imgproxy-retcat.assets.schwarz/hvlewo8XVNr9mww7nVzepzhyhQO5AkXeEqa1x_ilV-w/sm:1/exar:1:ce/w:1278/h:959/cz/M6Ly9wcm9kLWNhd/GFsb2ctbWVkaWEvYmcvMS8BREExMDA5RDlFQjg1MzAyNDkzMzc4OTZ/FQzNEQ0JDNDM0MUJCMUNGMzY4QzgxNDE3MEE2NDBFMTY3OTFEMjM1LnBuZw.png',
        'ref': '10058789',
        'offers': [
            {
                '@type': 'Offer',
                'priceCurrency': 'BGN',
                'price': 3.32,
                'itemCondition': 'NewCondition',
                'availability': 'OutOfStock',
                'url': 'https://www.lidl.bg/p/italiamo-kroasani/p10058789'
            }
        ]
    }
    """
    name = "lidl_bg"
    allowed_domains = ["lidl.bg"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q108169047",
                "name": "Lidl Bulgaria",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q151954",
                    "name": "Lidl",
                }
            }
        }
    }

    sitemap_urls = ["https://www.lidl.bg/static/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.lidl.bg/p/[^/]+/p\d+", "parse_sd"),
    ]
