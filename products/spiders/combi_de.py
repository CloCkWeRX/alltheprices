from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CombiDESpider(SitemapSpider, StructuredDataSpider):

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
