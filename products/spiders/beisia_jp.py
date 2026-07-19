import re
from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class BeisiaJPSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Beisia (Japan) (Q11336776).
    Fix #7.

    Sample output:
    {
        "name": "ブルボン アルフォート 115g 115g",
        "website": "https://netsuper.rakuten.co.jp/beisia/item/4901360363360/",
        "image": "https://netsuper.r10s.jp/item/beisia/60/4901360363360.jpg",
        "ref": "4901360363360",
        "sku": "4901360363360",
        "brand": "ブルボン",
        "price": 209.0,
        "proof_currency": "JPY",
        "offers": [
            {
                "@type": "Offer",
                "price": 209,
                "priceCurrency": "JPY"
            }
        ],
        "located_in_wikidata": "Q11336776"
    }
    """

    name = "beisia_jp"
    allowed_domains = ["netsuper.rakuten.co.jp"]
    start_urls = ["https://netsuper.rakuten.co.jp/beisia/"]

    item_attributes = {
        "located_in_wikidata": "Q11336776",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11336776",
                "name": "Beisia",
            }
        }
    }

    rules = (
        Rule(
            LinkExtractor(
                allow=[
                    r"/beisia/search/\d+/",
                ],
                deny=[
                    r"sort=",
                ]
            ),
            follow=True,
            process_request="use_playwright",
        ),
        Rule(
            LinkExtractor(
                allow=[
                    r"/beisia/item/(\d+)/",
                ]
            ),
            callback="parse_sd",
            process_request="use_playwright",
        ),
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

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, meta={"playwright": True})

    def use_playwright(self, request, response=None):
        request.meta["playwright"] = True
        return request

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q11336776"

        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

                if item.get("price") and item.get("proof_currency"):
                    break

        if item.get("price") is not None:
            try:
                price_str = str(item["price"]).replace(",", ".").strip()
                item["price"] = float(price_str)
            except ValueError:
                pass

        if not item.get("proof_currency"):
            item["proof_currency"] = "JPY"

        # Capture unique ref/sku
        ref_match = re.search(r"/beisia/item/(\d+)/", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)
            item["sku"] = ref_match.group(1)

        # Extract brand from ld_data if present
        brand_data = ld_data.get("brand")
        if brand_data:
            if isinstance(brand_data, dict):
                item["brand"] = brand_data.get("name")
            elif isinstance(brand_data, str):
                item["brand"] = brand_data

        yield item
