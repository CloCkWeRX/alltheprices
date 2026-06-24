from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BonpreuesclatESSpider(SitemapSpider, StructuredDataSpider):
    name = "bonpreuesclat_es"
    allowed_domains = ["compraonline.bonpreuesclat.cat"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11924747",
                "name": "Grup Bon Preu",
            }
        }
    }

    sitemap_urls = ["https://www.compraonline.bonpreuesclat.cat/robots.txt"]
    sitemap_rules = [
        (r"/products/.*/\d+$", "parse_sd"),
    ]
