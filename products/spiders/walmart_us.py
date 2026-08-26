import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class WalmartUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Walmart US (walmart.com) spider extracting products from sitemaps.
    Uses Scrapy-Playwright with Firefox to attempt bypassing bot protection and render product data.

    Sample output:
    {
        "name": "Freshness Guaranteed Frosted Sugar Cookies, Rainbow Cookie",
        "website": "https://www.walmart.com/ip/Freshness-Guaranteed-Frosted-Sugar-Cookies-Rainbow-Cookie-Multi-Color-Frosting-with-Sprinkles-Soft-Baked-Ready-to-Eat-13-5-oz-10-Count/13502519394",
        "ref": "13502519394",
        "sku": "13502519394",
        "brand": "Freshness Guaranteed",
        "offers": [
            {
                "@type": "Offer",
                "price": "3.98",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        ],
        "located_in_wikidata": "Q483551",
        "brand_wikidata": "Q483551"
    }
    """

    name = "walmart_us"
    allowed_domains = ["walmart.com"]
    sitemap_urls = [
        "https://www.walmart.com/sitemap_category.xml",
        "https://www.walmart.com/sitemap_product_03.xml",
    ]
    sitemap_rules = [
        (r"/ip/.*", "parse_sd"),
    ]

    located_in_wikidata = "Q483551"
    brand_wikidata = "Q483551"

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 2.0,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
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
            yield Request(url, self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if re.search(r"/ip/.*", request_or_item.url):
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_selector", 'script[type="application/ld+json"]', state="attached", timeout=15000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("offers"):
            yield item
            return

        for offer in item.get("offers", []):
            if isinstance(offer, dict):
                offer["priceCurrency"] = "USD"

        item["located_in_wikidata"] = self.located_in_wikidata

        yield item
