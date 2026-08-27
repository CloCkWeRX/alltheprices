import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class CoopSESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Coop Sweden (coop.se).
    Wikidata: Q1510161 (Kooperativa Förbundet)
    Fix #122.
    """

    name = "coop_se"
    allowed_domains = ["coop.se"]
    sitemap_urls = ["https://www.coop.se/sitemap.xml"]
    sitemap_follow = [r"sitemap_products\.xml"]
    sitemap_rules = [
        (r"/handla/varor/.*-(\d+)$", "parse_sd"),
    ]

    dataset_attributes = {
        "source": "structured_data",
        "wikidata": "Q1510161",
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

    item_attributes = {
        "proof_currency": "SEK",
        "located_in_wikidata": "Q1510161",
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
                            PageMethod(
                                "wait_for_selector",
                                'script[type="application/ld+json"]',
                                state="attached",
                                timeout=10000,
                            ),
                        ],
                    },
                )
            return

        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if request_or_item.callback == self.parse_sd:
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod(
                            "wait_for_selector",
                            'script[type="application/ld+json"]',
                            state="attached",
                            timeout=10000,
                        ),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        item["proof_currency"] = "SEK"
        item["located_in_wikidata"] = "Q1510161"

        if ld_data:
            sku = ld_data.get("sku")
            if sku:
                item["ref"] = str(sku).strip()
                item["sku"] = str(sku).strip()

            brand_obj = ld_data.get("brand")
            if isinstance(brand_obj, dict) and brand_obj.get("name"):
                item["brand"] = brand_obj["name"].strip()
            elif isinstance(brand_obj, str):
                item["brand"] = brand_obj.strip()

        if not item.get("ref"):
            match = re.search(r"-(\d+)$", response.url)
            if match:
                item["ref"] = match.group(1)
                item["sku"] = match.group(1)

        brand_name = item.get("brand") or ""
        if "coop" in brand_name.lower():
            item["brand_wikidata"] = "Q1510161"
        else:
            item.pop("brand_wikidata", None)

        yield item
