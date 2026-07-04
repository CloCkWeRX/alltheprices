from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product


class PlusNLSpider(SitemapSpider):
    name = "plus_nl"
    allowed_domains = ["plus.nl"]
    sitemap_urls = ["https://www.plus.nl/ECP_Sitemap_Engine/rest/Sitemap/index"]
    sitemap_rules = [
        (r"/product/", "parse_product"),
    ]

    custom_settings = {
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "CONCURRENT_REQUESTS": 2,
    }

    def _parse_sitemap(self, response):
        if "index" in response.url:
            for sitemap in response.xpath("//*[local-name()='sitemap']"):
                loc = sitemap.xpath("./*[local-name()='loc']/text()").get()
                if "product" in loc:
                    yield Request(loc, callback=self._parse_sitemap)
        else:
            for request_or_item in super()._parse_sitemap(response):
                if isinstance(request_or_item, Request):
                    if "/product/" in request_or_item.url:
                        request_or_item.meta["playwright"] = True
                        request_or_item.meta["playwright_include_body"] = True
                        request_or_item.meta["playwright_page_methods"] = [
                            PageMethod("wait_for_selector", ".btn-cookies-accept", timeout=20000),
                            PageMethod("click", ".btn-cookies-accept"),
                            PageMethod("wait_for_selector", "h1 span.js-screen-title", timeout=20000),
                        ]
                    yield request_or_item
                else:
                    yield request_or_item

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Name
        name = response.css("h1 span.js-screen-title::text").get()
        if not name:
            name = response.css("h1::text").get()
        product["name"] = name.strip() if name else None

        # Price
        price_integer = response.css(".product-header-price-integer span::text").get()
        price_decimals = response.css(".product-header-price-decimals span::text").get()
        if price_integer and price_decimals:
            price_integer = price_integer.replace(".", "").strip()
            price_str = f"{price_integer}.{price_decimals.strip()}"
            try:
                product["price"] = float(price_str)
            except ValueError:
                pass

        # Image
        image = response.css(".product-header-image img::attr(src)").get()
        product["image"] = image

        # Ref
        ref = response.url.split("-")[-1]
        product["ref"] = ref

        product["located_in_wikidata"] = "Q1978981"
        product["proof_currency"] = "EUR"

        if product.get("name"):
            yield product
