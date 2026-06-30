from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider


class ErewhonUSSpider(SitemapSpider, StructuredDataSpider):
    name = "erewhon_us"
    allowed_domains = ["ship.erewhon.com"]
    sitemap_urls = ["https://ship.erewhon.com/sitemap.xml"]
    sitemap_rules = [(r"/products/", "parse_sd")]

    item_attributes = {
        "brand": "Erewhon",
        "brand_wikidata": "Q105628552",
        "extras": {
            "seller": "Erewhon",
        },
    }
