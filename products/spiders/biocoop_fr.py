from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BiocoopFRSpider(SitemapSpider, StructuredDataSpider):
    name = "biocoop_fr"
    allowed_domains = ["biocoop.fr"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2904039",
                "name": "Biocoop",
            }
        }
    }

    sitemap_urls = ["https://www.biocoop.fr/robots.txt"]
    sitemap_rules = [
        (r"https://www.biocoop.fr/[\w-]+.html", "parse_sd"),
    ]
