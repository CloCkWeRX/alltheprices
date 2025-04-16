from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CondisESSpider(SitemapSpider, StructuredDataSpider):
    name = "condis_es"
    allowed_domains = ["condisline.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q57417581",
                "name": "Condis",
            }
        }
    }

    sitemap_urls = ["https://condisline.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.condisline.com/(.*).jsp", "parse_sd"),
    ]
