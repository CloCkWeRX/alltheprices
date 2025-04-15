from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BotanicFRSpider(SitemapSpider, StructuredDataSpider):
    name = "botanic_fr"
    allowed_domains = ["botanic.com"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q2911642", "name": "Botanic"}
        }
    }

    sitemap_urls = ["https://www.botanic.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.botanic.com/produit/\d+/[\w]+.html", "parse_sd"),
    ]
