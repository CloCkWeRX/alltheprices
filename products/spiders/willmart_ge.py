from scrapy.spiders import SitemapSpider

# from products.categories import PaymentMethods, map_payment
from products.structured_data_spider import StructuredDataSpider


class WillmartGESpider(SitemapSpider, StructuredDataSpider):
    name = "willmart_ge"
    allowed_domains = ["willmart.ge"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q118793042", "name": "Willmart"}
        }
    }

    sitemap_urls = ["https://willmart.ge/robots.txt"]
    sitemap_rules = [
        (r"https://willmart.ge/shop/[\w-]+/[\w-]+", "parse_sd"),
    ]
