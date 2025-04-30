from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CheckersZASpider(SitemapSpider, StructuredDataSpider):
    name = "checkers_za"
    allowed_domains = ["checkers.co.za"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5089126",
                "name": "Checkers",
            }
        }
    }

    sitemap_urls = ["https://www.checkers.co.za/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.checkers.co.za/All-Departments/(.*)/p/[\w-]+", "parse_sd"),
    ]
