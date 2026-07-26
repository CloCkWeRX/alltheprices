import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class CitygrossSESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for City Gross (Sweden).
    Wikidata: Q10452390

    @url https://www.citygross.se/matvaror/fisk-och-skaldjur/fisk/falkenberg-kallr%C3%B6kt-lax-skivad-p101330534_ST
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "citygross_se"
    allowed_domains = ["citygross.se"]
    sitemap_urls = ["https://www.citygross.se/sitemap.xml"]
    sitemap_rules = [(r"-p(\d+[^/]*)$", "parse_sd")]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q10452390",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q10452390",
                "name": "City Gross",
            }
        },
    }

    convert_microdata = True

    def start_requests(self):
        # Yield the sample product detail page URL with playwright=True to ensure correct rendering
        yield Request(
            "https://www.citygross.se/matvaror/fisk-och-skaldjur/fisk/falkenberg-kallr%C3%B6kt-lax-skivad-p101330534_ST",
            callback=self.parse_sd,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", ".product-single-container", timeout=20000),
                ]
            },
        )
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # If matched as a product page, parse it
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.callback = self.parse_sd
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_selector", ".product-single-container", timeout=20000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q10452390"

        # Ensure currency and price are promoted
        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]
            elif not isinstance(offers, list):
                offers = []

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
            item["proof_currency"] = "SEK"

        # Capture unique ref/sku
        ref_match = re.search(r"-p(\d+[^/]*)$", response.url)
        if ref_match:
            item["ref"] = "p" + ref_match.group(1)
            item["sku"] = "p" + ref_match.group(1)
        elif not item.get("ref") and item.get("sku"):
            item["ref"] = item["sku"]

        # Ensure brand name is set nicely
        if not item.get("brand") and ld_data.get("brand"):
            brand_data = ld_data["brand"]
            if isinstance(brand_data, dict):
                item["brand"] = brand_data.get("name")
            elif isinstance(brand_data, str):
                item["brand"] = brand_data

        yield item
