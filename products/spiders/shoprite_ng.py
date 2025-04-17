from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class ShopriteNGSpider(SitemapSpider, StructuredDataSpider):
    name = "shoprite_ng"
    allowed_domains = ["shoprite.ng"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q1857639", "name": "Shoprite"}
        }
    }

    sitemap_urls = ["https://shoprite.ng/robots.txt"]
    sitemap_rules = [
        (r"https://shoprite.ng/product/[\w-]+/", "parse_sd"),
    ]
