from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class AptekaMagnitRUSpider(SitemapSpider, StructuredDataSpider):
    """
    Magnit Pharmacy (Russia) spider.
    Fixes #42.
    Wikidata: Q120262563
    Parent: Magnit (Q940518)
    """

    name = "apteka_magnit_ru"
    allowed_domains = ["apteka.magnit.ru"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q120262563",
                "name": "Magnit Pharmacy",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q940518",
                    "name": "Magnit",
                },
            }
        }
    }

    sitemap_urls = ["https://apteka.magnit.ru/sitemap_index.xml"]
    sitemap_rules = [
        (r"/product/(.*)", "parse_sd"),
    ]
