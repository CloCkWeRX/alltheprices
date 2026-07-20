import codecs
import re
from typing import Iterable

import chompjs
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class TavriaUASpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Tavria V (Ukraine).
    Wikidata: Q7689159
    """

    name = "tavria_ua"
    allowed_domains = ["tavriav.ua", "tavriav.org"]
    located_in_wikidata = "Q7689159"

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
    }

    rules = (
        # Match product pages
        Rule(
            LinkExtractor(allow=(r"/p/",)),
            callback="parse_sd",
            process_request="use_playwright",
        ),
    )

    def start_requests(self):
        # We start by requesting the homepage with Playwright
        yield scrapy.Request(
            url="https://www.tavriav.ua/",
            callback=self._parse,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 3000),
                ],
            },
        )

    def use_playwright(self, request, response):
        request.meta["playwright"] = True
        request.meta["playwright_page_methods"] = [
            PageMethod("wait_for_timeout", 3000),
        ]
        return request

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Try standard LD-JSON first (though it may be empty on this Next.js site)
        yield from super().iter_linked_data(response)

        # Parse Next.js hydration scripts
        scripts = response.xpath('//script[contains(text(), "self.__next_f.push")]/text()').getall()
        for script in scripts:
            # We look for something that contains product details
            if '"product"' not in script:
                continue

            # Extract Next.js push content
            matches = re.findall(r'self\.__next_f\.push\(\[\d+,"(.*?)"\]\)', script, re.DOTALL)
            for inner_str in matches:
                try:
                    # Next.js push strings can have prefixes like '8:'
                    if ":" in inner_str[:3]:
                        inner_str = inner_str.split(":", 1)[1]

                    decoded_str = codecs.decode(inner_str, "unicode_escape")
                    # Correct Cyrillic mojibake (interpreted as latin-1 instead of utf-8)
                    try:
                        corrected_str = decoded_str.encode("latin1").decode("utf-8")
                    except Exception:
                        corrected_str = decoded_str

                    data = chompjs.parse_js_object(corrected_str)
                    product = self._find_product_detail(data)
                    if product:
                        # Construct a Schema.org Product structure for StructuredDataSpider to process
                        ld_item = {
                            "@type": "Product",
                            "name": product.get("name"),
                            "brand": product.get("brand"),
                            "sku": str(product.get("sku") or product.get("idProduct") or ""),
                            "image": product.get("photosUrl") or [],
                            "description": product.get("description"),
                            "offers": {
                                "@type": "Offer",
                                "price": product.get("price"),
                                "priceCurrency": "UAH",
                                "availability": "https://schema.org/InStock" if product.get("isAvailable", True) else "https://schema.org/OutOfStock",
                            },
                        }
                        yield ld_item
                except Exception:
                    continue

    def _find_product_detail(self, obj):
        if isinstance(obj, dict):
            if "product" in obj and isinstance(obj["product"], dict) and "name" in obj["product"]:
                return obj["product"]
            for v in obj.values():
                res = self._find_product_detail(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_product_detail(item)
                if res:
                    return res
        return None

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q7689159"

        if "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                price = offers.get("price")
                if price:
                    item["price"] = str(price)

                currency = offers.get("priceCurrency")
                if currency:
                    item["proof_currency"] = currency

        if not item.get("name"):
            item["name"] = response.xpath('//h1/text()').get() or response.xpath('//meta[@property="og:title"]/@content').get()

        if item.get("name"):
            item["name"] = item["name"].strip()

        yield item
