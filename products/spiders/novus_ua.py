from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class NovusUASpider(SitemapSpider, StructuredDataSpider):
    name = "novus_ua"
    allowed_domains = ["novus.ua"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q116748340", "name": "Novus"}
        }
    }

    sitemap_urls = ["https://novus.ua/sitemap.xml"]
    sitemap_rules = [
        (r"https://novus.ua/[\w-]+.html", "parse_sd"),
    ]
