import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SainsburysGBSpider(SitemapSpider, StructuredDataSpider):
    """
    Sainsbury's UK (sainsburys.co.uk) spider extracting products from sitemaps.
    Uses Playwright for both sitemaps and product detail pages to bypass Cloudflare protection and access JSON-LD structured data.
    """

    name = "sainsburys_gb"
    allowed_domains = ["sainsburys.co.uk"]
    sitemap_urls = ["https://www.sainsburys.co.uk/sitemap.xml"]
    sitemap_follow = [
        r"shelf_sitemap\.xml",
        r"offers_sitemap\.xml",
        r"obs_sitemap\.xml",
    ]
    sitemap_rules = [
        (r"/gol-ui/product/([^/]+)$", "parse_sd"),
    ]

    dataset_attributes = {
        "source": "structured_data",
        "wikidata": "Q152096",
    }

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
    }

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(
                    url,
                    callback=self.parse_sd,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", 'script[type="application/ld+json"]', state="attached", timeout=10000),
                        ],
                    },
                )
            return

        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
                meta={"playwright": True},
            )

    def _parse_sitemap(self, response):
        """
        Override _parse_sitemap to route all sitemap sub-requests and product requests through Playwright.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                if request_or_item.callback == self.parse_sd:
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_selector", 'script[type="application/ld+json"]', state="attached", timeout=10000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # Extract price and proof_currency from offers if available
        if ld_data:
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    try:
                        item["price"] = float(str(offer["price"]).replace(",", ".").strip())
                    except ValueError:
                        pass
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

        if item.get("price") and not item.get("proof_currency"):
            item["proof_currency"] = "GBP"

        # Ensure ref / sku is captured
        if not item.get("ref"):
            if item.get("sku"):
                item["ref"] = str(item["sku"])
            else:
                sku_match = re.search(r"/product/.*-?(\d+)$", response.url)
                if sku_match:
                    item["ref"] = sku_match.group(1)

        # Set GTIN if numerical ref / sku matches GTIN format
        if item.get("ref") and re.match(r"^\d{8,14}$", str(item["ref"])):
            item["gtin"] = str(item["ref"])

        # Extract brand if missing
        if not item.get("brand") and ld_data:
            brand_obj = ld_data.get("brand")
            if isinstance(brand_obj, dict):
                item["brand"] = brand_obj.get("name")
            elif isinstance(brand_obj, str):
                item["brand"] = brand_obj

        yield item
