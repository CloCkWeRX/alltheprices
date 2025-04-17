from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class AlnaturaDESpider(SitemapSpider, StructuredDataSpider):
    name = "alnatura_de"
    allowed_domains = ["alnatura.de"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q876811",
                "name": "Alnatura",
            }
        }
    }

    sitemap_urls = ["https://www.alnatura.de/robots.txt"]
    sitemap_rules = [
        (r"https://www.alnatura.de/de-de/produkte/alle-produkte/[\w-]+/[\w-]+/[\w-]+", "parse_sd"),
    ]
