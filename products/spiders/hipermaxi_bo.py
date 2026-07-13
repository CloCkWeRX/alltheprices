import re
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class HipermaxiBOSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Hipermaxi (Bolivia).
    Wikidata: Q81968262
    The site is a Next.js application protected by Radware.
    Requires Playwright for rendering and bypassing bot detection.
    """
    name = "hipermaxi_bo"
    allowed_domains = ["hipermaxi.com"]
    # Starting with a few major regions and categories
    start_urls = [
        "https://www.hipermaxi.com/santa-cruz/hipermaxi-roca-y-coronado/categoria/abarrotes",
        "https://www.hipermaxi.com/santa-cruz/hipermaxi-roca-y-coronado/categoria/bebidas",
        "https://www.hipermaxi.com/la-paz/hipermaxi-calacoto/categoria/abarrotes",
        "https://www.hipermaxi.com/la-paz/hipermaxi-calacoto/categoria/bebidas",
        "https://www.hipermaxi.com/cochabamba/hipermaxi-blanco-galindo/categoria/abarrotes",
        "https://www.hipermaxi.com/cochabamba/hipermaxi-blanco-galindo/categoria/bebidas",
    ]

    rules = (
        Rule(LinkExtractor(allow=r"/categoria/"), follow=True, process_request="process_playwright_request"),
        Rule(LinkExtractor(allow=r"/producto/(\d+)/"), callback="parse_sd", process_request="process_playwright_request"),
    )

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
    }

    item_attributes = {
        "located_in_wikidata": "Q81968262",
        "proof_currency": "BOB",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, meta={"playwright": True, "playwright_include_page": False})

    def process_playwright_request(self, request, response):
        request.meta["playwright"] = True
        request.meta["playwright_include_page"] = False
        return request

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q81968262"
        item["proof_currency"] = "BOB"

        if not item.get("name"):
            item["name"] = response.css("h1::text").get()

        # Promote price from offers if not already set
        if not item.get("price") and item.get("offers"):
            offers = item["offers"]
            if isinstance(offers, list) and len(offers) > 0:
                item["price"] = str(offers[0].get("price"))

        if not item.get("price"):
            # Try to find price text in the page
            price_text = response.css(".text-primary.text-2xl::text").get()
            if not price_text:
                # Look for Bs. followed by a number, possibly with decimals
                price_text = response.xpath('//*[contains(text(), "Bs.")]/text()').get()

            if price_text:
                # Improved regex to handle whole numbers and decimals
                price_match = re.search(r"(\d+(?:[,.]\d+)?)", price_text)
                if price_match:
                    item["price"] = price_match.group(1).replace(",", ".")

        if not item.get("ref"):
            match = re.search(r"/producto/(\d+)/", response.url)
            if match:
                item["ref"] = match.group(1)

        if not item.get("image"):
            image_url = response.css("main img[alt*='producto']::attr(src)").get()
            if not image_url:
                image_url = response.css("main img::attr(src)").get()
            if image_url:
                item["image"] = response.urljoin(image_url)

        yield item
