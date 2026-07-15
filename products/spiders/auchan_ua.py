from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AuchanUASpider(SitemapSpider, StructuredDataSpider):
    name = "auchan_ua"
    allowed_domains = ["auchan.ua"]
    user_agent = FIREFOX_LATEST

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4073419",
                "name": "Auchan",
            }
        }
    }

    sitemap_urls = [
        "https://auchan.ua/media/images.xml",
    ]
    sitemap_rules = [
        (r"-(\d+)/$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data):
        item["proof_currency"] = "UAH"
        yield item
