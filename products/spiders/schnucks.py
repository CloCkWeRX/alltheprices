from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class SchnucksSpider(SitemapSpider, StructuredDataSpider):
    name = "schnucks"
    allowed_domains = ["schnucks.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7431920",
                "name": "Schnucks",
            }
        }
    }

    sitemap_urls = ["https://schnucks.com/robots.txt"]
    sitemap_rules = [
        (r"https://schnucks\.com/products/(\d+)", "parse_sd"),
    ]
