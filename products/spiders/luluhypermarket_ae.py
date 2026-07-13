from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LuluhypermarketAESpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Lulu Hypermarket (UAE).
    Wikidata: Q6702930

    Sample output structured data:
    {
        "name": "Cashew Nut W240 500 g",
        "website": "https://gcc.luluhypermarket.com/en-ae/cashew-nut-w240-500-g/p/2068588-ea/",
        "image": "https://bf1af2.akinoncloudcdn.com/products/2024/09/20/53091/b5a75277-acbd-4a77-9859-fed443f44a64.jpg",
        "ref": "2068588-ea",
        "sku": "2068588_EA",
        "brand": "LuLu Roastery",
        "located_in_wikidata": "Q6702930",
        "price": "35.000",
        "proof_currency": "aed"
    }
    """

    name = "luluhypermarket_ae"
    allowed_domains = ["luluhypermarket.com"]
    start_urls = ["https://gcc.luluhypermarket.com/en-ae/grocery/"]

    user_agent = FIREFOX_LATEST
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    rules = (
        Rule(
            LinkExtractor(allow=r"/p/(\d+)-ea/"),
            callback="parse_sd",
        ),
        Rule(
            LinkExtractor(allow=r"/en-ae/grocery-.*"),
            follow=True,
        ),
    )

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q6702930"

        # Refinement for ref if needed, usually StructuredDataSpider picks it up from SKU or similar.
        # In the test output, SKU was "2068588_EA" and url had "2068588-ea".

        if not item.get("price") and "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict):
                item["price"] = offers.get("price")
                item["proof_currency"] = offers.get("priceCurrency")

        if item.get("proof_currency"):
            item["proof_currency"] = item["proof_currency"].upper()

        yield item
