import re
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ComodiIidaJPSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Comodi-iida (Japan).
    Fixes #4.
    Wikidata: Q11302699

    Sample output structured data:
    {
        "name": "新潟県産コシヒカリ 5ｋｇ※お一人様1点まで",
        "website": "https://netsuper.rakuten.co.jp/comodi-iida/item/3501035/",
        "image": "https://netsuper.r10s.jp/item/comodi-iida/35/3501035.jpg",
        "ref": "3501035",
        "brand": "コモディイイダ",
        "brand_wikidata": "Q11302699",
        "price": 2980.0,
        "proof_currency": "JPY",
        "offers": [
            {
                "@type": "Offer",
                "price": 2980,
                "priceCurrency": "JPY"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11302699",
                "name": "コモディイイダ"
            }
        }
    }
    """

    name = "comodi_iida_jp"
    allowed_domains = ["netsuper.rakuten.co.jp"]

    # Since Akamai blocks standard Scrapy/Twisted TLS handshake, we utilize Scrapy-Playwright
    # with Firefox browser engine. This perfectly mimics a real browser and bypasses the 403 block.
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

    sitemap_urls = ["https://netsuper.rakuten.co.jp/contents/sitemap.xml"]
    sitemap_rules = [
        (r"/comodi-iida/item/(\d+)/", "parse_sd"),
    ]

    item_attributes = {
        "brand": "コモディイイダ",
        "brand_wikidata": "Q11302699",
        "proof_currency": "JPY",
        "located_in_wikidata": "Q1490",  # Tokyo, Japan
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11302699",
                "name": "コモディイイダ",
            }
        },
    }

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
            yield request_or_item

    def sitemap_filter(self, entries):
        for entry in entries:
            # Only process item URLs for Comodi-iida
            if "/comodi-iida/item/" in entry["loc"]:
                yield entry

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        # Skip error pages or pages with missing name
        if not item.get("name") or "/error" in response.url:
            return

        # We want to make sure the brand is set to Comodi-iida instead of potential sub-brands or descriptors
        # We also want to merge the standard item attributes.
        item["brand"] = self.item_attributes["brand"]
        item["brand_wikidata"] = self.item_attributes["brand_wikidata"]
        item["proof_currency"] = self.item_attributes["proof_currency"]
        item["located_in_wikidata"] = self.item_attributes["located_in_wikidata"]
        item["extras"] = {**item.get("extras", {}), **self.item_attributes["extras"]}

        # If offers is present, promote the price to top-level if needed
        if "offers" in item and item["offers"]:
            offers = item["offers"]
            offer = offers[0] if isinstance(offers, list) else offers
            if "price" in offer:
                try:
                    item["price"] = float(offer["price"])
                except (ValueError, TypeError):
                    pass

        # Clean the ref from URL if missing or malformed
        if not item.get("ref"):
            ref_match = re.search(r"/comodi-iida/item/(\d+)/", response.url)
            if ref_match:
                item["ref"] = ref_match.group(1)

        yield item
