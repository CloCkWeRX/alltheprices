import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class TescoGBSpider(SitemapSpider, StructuredDataSpider):
    """
    Tesco UK (tesco.com) spider extracting products from sitemaps.
    Uses Scrapy-Playwright with Firefox to render structured data script tags on product detail pages.
    """

    name = "tesco_gb"
    allowed_domains = ["tesco.com"]
    sitemap_urls = ["https://www.tesco.com/sitemaps/en-GB/groceries/products-index.xml"]
    sitemap_rules = [
        (r"/shop/en-GB/products/(\d+)", "parse_sd"),
    ]

    dataset_attributes = {
        "source": "structured_data",
        "wikidata": "Q487494",
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
        "DOWNLOAD_DELAY": 0.5,
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
                            PageMethod("wait_for_selector", 'script[type="application/ld+json"]', state="attached", timeout=15000),
                        ],
                    },
                )
            return

        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
            )

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if request_or_item.callback == self.parse_sd:
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_selector", 'script[type="application/ld+json"]', state="attached", timeout=15000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # Extract price and currency from offers if missing
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

        if not item.get("proof_currency"):
            item["proof_currency"] = "GBP"

        if not item.get("ref"):
            if item.get("sku"):
                item["ref"] = str(item["sku"])
            else:
                match = re.search(r"/products/(\d+)", response.url)
                if match:
                    item["ref"] = match.group(1)

        if item.get("ref") and re.match(r"^\d{8,14}$", str(item["ref"])):
            item["gtin"] = str(item["ref"])

        # Extract brand if missing or set wikidata for Tesco brand
        if not item.get("brand") and ld_data:
            brand_obj = ld_data.get("brand")
            if isinstance(brand_obj, dict):
                item["brand"] = brand_obj.get("name")
            elif isinstance(brand_obj, str):
                item["brand"] = brand_obj

        if not item.get("brand"):
            item["brand"] = "Tesco"

        if item.get("brand") and "tesco" in item["brand"].lower():
            item["brand_wikidata"] = "Q487494"

        item["located_in_wikidata"] = "Q487494"

        yield item
