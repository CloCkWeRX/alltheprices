from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AvRUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Azbuka Vkusa (av.ru) (Russia).
    Wikidata: Q4058209

    @url https://av.ru/i/589345
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "av_ru"
    allowed_domains = ["av.ru"]
    sitemap_urls = ["https://av.ru/sitemap.xml"]
    sitemap_rules = [
        (r"/i/(\d+)", "parse_sd"),
    ]

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
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1.5,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    item_attributes = {
        "located_in_wikidata": "Q4058209",
        "brand_wikidata": "Q4058209",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4058209",
                "name": "Azbuka Vkusa",
            }
        },
    }

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(url, self.parse_sd, meta={"playwright": True})
            return

        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data: dict, **kwargs):
        if offers := item.get("offers"):
            if isinstance(offers, dict):
                offers = [offers]
            elif not isinstance(offers, list):
                offers = []
            for offer in offers:
                if isinstance(offer, dict) and not offer.get("priceCurrency"):
                    offer["priceCurrency"] = "RUB"

        yield from super().post_process_item(item, response, ld_data)
