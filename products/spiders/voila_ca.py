from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class VoilaCASpider(SitemapSpider, StructuredDataSpider):
    """
    Voilà by Sobeys (Canada) spider.
    Fixes #261.
    Wikidata: Q1143340 (Sobeys)
    Parent: Empire Company (Q5374063)

    Sample output:
    {
        "name": "Mini Carrots Peeled 907 g",
        "website": "https://voila.ca/products/mini-carrots-peeled-907-g/113450EA",
        "image": "https://voila.ca/images-v3/2d92d19c-0354-49c0-8a91-5260ed0bf531/b5ec2c4a-03f5-48f4-a521-1ada346a01fb/500x500.jpg",
        "ref": "113450EA",
        "offers": [
            {
                "@type": "Offer",
                "price": "5.99",
                "priceCurrency": "CAD",
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1143340",
                "name": "Sobeys",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q5374063",
                    "name": "Empire Company Limited"
                }
            }
        }
    }
    """

    name = "voila_ca"
    allowed_domains = ["voila.ca"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1143340",
                "name": "Sobeys",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q5374063",
                    "name": "Empire Company Limited",
                },
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    sitemap_urls = [
        "https://voila.ca/sitemaps/sitemap-products-part1.xml",
        "https://voila.ca/sitemaps/sitemap-products-part2.xml",
    ]
    sitemap_rules = [
        (r"/products/.*?/(\w+)$", "parse_sd"),
    ]
