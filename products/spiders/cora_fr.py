from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CoraFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cora_fr"
    allowed_domains = ["cora.fr"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q686643",
                "name": "Cora",
            }
        }
    }

    sitemap_urls = ["https://www.cora.fr/robots.txt"]
    sitemap_rules = [
        (r"https://www.cora.fr/article/[\d]+/[\w-]+.html", "parse_sd"),
    ]
