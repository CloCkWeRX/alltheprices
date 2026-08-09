from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class TottusSpider(SitemapSpider, StructuredDataSpider):
    name = "tottus"
    allowed_domains = ["tottus.cl", "tottus.com.pe", "tottus.com"]
    item_attributes = {
        "brand_wikidata": "Q7828510",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7828510",
                "name": "Tottus",
            }
        }
    }

    sitemap_urls = [
        "https://www.tottus.cl/robots.txt",
        "https://www.tottus.com.pe/robots.txt",
    ]
    sitemap_rules = [
        (r"/articulo/", "parse_sd"),
    ]
