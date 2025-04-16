from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class SeijoishiiJPSpider(SitemapSpider, StructuredDataSpider):
    name = "seijoishii_jp"
    allowed_domains = ["seijoishii.com"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q11495410", "name": "Seijo Ishii"}
        }
    }

    sitemap_urls = ["https://seijoishii.com/robots.txt"]
    sitemap_rules = [
        (r"https://seijoishii.com/products/\d+", "parse_sd"),
    ]
