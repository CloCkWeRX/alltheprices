from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class GiantTigerSpider(SitemapSpider, StructuredDataSpider):
    name = "giant_tiger"
    allowed_domains = ["gianttiger.com"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q5558429", "name": "Giant Tiger"}
        }
    }

    sitemap_urls = ["https://www.gianttiger.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.gianttiger.com/products/.*", "parse_sd"),
    ]
