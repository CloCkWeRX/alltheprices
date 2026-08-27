from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class GoasiaNetSpider(SitemapSpider, StructuredDataSpider):
    name = "goasia_net"
    allowed_domains = ["goasia.net"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q105622956",
                "name": "Go Asia",
            }
        }
    }

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": ["--disable-blink-features=AutomationControlled"],
        },
    }

    sitemap_urls = ["https://goasia.net/sitemap.xml"]
    sitemap_rules = [
        (r"https://goasia.net/(?:en|de)/.*/\d+-[\w-]+\.html", "parse_sd_playwright"),
    ]

    def __init__(self, *args, **kwargs):
        self.start_urls = kwargs.pop("start_urls", [])
        if isinstance(self.start_urls, str):
            self.start_urls = [self.start_urls]
        super().__init__(*args, **kwargs)

    def start_requests(self):
        if self.start_urls:
            for url in self.start_urls:
                yield Request(
                    url,
                    callback=self.parse_sd_playwright,
                    meta={"playwright": True, "playwright_include_page": True},
                )
        else:
            yield from super().start_requests()

    async def parse_sd_playwright(self, response):
        page = response.meta.get("playwright_page")
        if not page:
            for item in self.parse_sd(response):
                yield item
            return

        try:
            try:
                await page.wait_for_selector("h1:not(:has-text('Attention Required'))", timeout=30000)
            except Exception:
                self.logger.info("Timeout waiting for non-Cloudflare H1, attempting to parse anyway")

            content = await page.content()
            response = response.replace(body=content.encode("utf-8"))

            for item in self.parse_sd(response):
                yield item
        finally:
            await page.close()

    def _build_request(self, rule, url):
        req = super()._build_request(rule, url)
        if req.callback == self.parse_sd_playwright:
            req.meta.update({"playwright": True, "playwright_include_page": True})
        return req
