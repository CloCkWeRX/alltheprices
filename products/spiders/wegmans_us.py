import re
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class WegmansUSSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Wegmans (USA).
    Extracts product data from product detail pages using Playwright.
    Wikidata: Q11288478 (Wegmans)

    Sample output:
    {
        "name": "Reese's Egg Peanut Butter Milk Chocolate",
        "description": "Reese's Peanut Butter Egg Candy--Holiday 1.2 OZ",
        "brand": "Reese's",
        "ref": "806445",
        "gtin": "00034000004751",
        "image": "https://images.wegmans.com/is/image/wegmanscsprod/806445_PrimaryImage?v=9fffae662fc520821596e64f042e8ccbfb22e52e",
        "website": "https://www.wegmans.com/shop/product/806445-Peanut-Butter-Egg",
        "located_in_wikidata": "Q11288478"
    }
    """

    name = "wegmans_us"
    allowed_domains = ["wegmans.com"]
    start_urls = ["https://www.wegmans.com/shop/categories"]

    rules = (
        # Follow category pages
        Rule(LinkExtractor(allow=r"/shop/categories/\d+"), process_request="use_playwright"),
        # Parse product detail pages
        Rule(LinkExtractor(allow=r"/shop/product/(\d+)-[^/]+$"), callback="parse_sd", process_request="use_playwright"),
    )

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q11288478",
    }

    def start_requests(self):
        """
        Override start_requests to route initial request through Playwright.
        """
        for url in self.start_urls:
            yield Request(url, meta={"playwright": True})

    def use_playwright(self, request, response):
        """
        Force Playwright rendering for both followed category links and product pages.
        """
        request.meta["playwright"] = True
        return request

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q11288478"

        # Only set brand_wikidata if it is a Wegmans store brand
        brand_name = item.get("brand") or ""
        if "wegmans" in brand_name.lower():
            item["brand_wikidata"] = "Q11288478"
        else:
            item.pop("brand_wikidata", None)

        # Explicitly set currency to USD
        item["proof_currency"] = "USD"

        # Map gtin13/gtin to gtin
        if ld_data.get("gtin13"):
            item["gtin"] = ld_data["gtin13"]
        elif ld_data.get("gtin"):
            item["gtin"] = ld_data["gtin"]

        # Ensure name and description are stripped of excess whitespace
        if item.get("name"):
            item["name"] = item["name"].strip()
        if item.get("description"):
            item["description"] = item["description"].strip()

        yield item
