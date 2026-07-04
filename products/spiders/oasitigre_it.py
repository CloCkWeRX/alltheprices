import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy_playwright.page import PageMethod
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class OasitigreITSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Oasi Tigre (Italy).
    Website: https://www.oasitigre.it/
    This is an SPA, so it requires Playwright for rendering.
    Product data is primarily found in data attributes of the .js-product-content element (main product)
    or .product-card elements (listings).
    We set a default store cookie to ensure prices are available.
    """

    name = "oasitigre_it"
    allowed_domains = ["oasitigre.it"]
    start_urls = ["https://www.oasitigre.it/it/spesa/reparti.html"]

    # Default store ID (Ascoli Piceno)
    DEFAULT_STORE_ID = "425"

    rules = (
        Rule(LinkExtractor(allow=r"/it/spesa/reparti/")),
        Rule(
            LinkExtractor(allow=r"/prodotti/.*?-(\d+)\.html$"),
            callback="parse_product_pre",
        ),
    )

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type in ["font", "media"],
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                cookies={
                    "idPdv": self.DEFAULT_STORE_ID,
                    "tipoSpesa": "RITIRA",
                },
            )

    def parse_product_pre(self, response):
        yield Request(
            response.url,
            cookies={
                "idPdv": self.DEFAULT_STORE_ID,
                "tipoSpesa": "RITIRA",
            },
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    # Wait for either the main product content or any product card to appear
                    PageMethod("wait_for_selector", ".js-product-content, .product-card", timeout=15000),
                ],
            },
            callback=self.parse_product,
            dont_filter=True,
        )

    def parse_product(self, response):
        ref_match = re.search(r"-(\d+)\.html$", response.url)
        target_ref = ref_match.group(1) if ref_match else None

        # Look for the main product container
        main_content = response.css(f'.js-product-content[data-prodid="{target_ref}"]')
        if not main_content:
            main_content = response.css(".js-product-content")

        # Also look for the product card that matches the ID in the URL (often present in a swiper or list)
        product_card = response.css(f'.product-card[data-productid="{target_ref}"]')

        if main_content or product_card:
            item = Product()
            item["website"] = response.url
            item["proof_currency"] = "EUR"

            # Prefer data from product_card if available as it often has more attributes
            source = product_card[0] if product_card else main_content[0]

            item["name"] = source.attrib.get("data-title") or source.attrib.get("data-productname")
            item["ref"] = source.attrib.get("data-productid") or source.attrib.get("data-prodid")
            item["brand"] = source.attrib.get("data-brand")

            if not item["name"]:
                item["name"] = response.css("h1::text").get()
            if item["name"]:
                item["name"] = item["name"].strip()

            # Extraction logic for price
            price = source.attrib.get(f"data-price-value{self.DEFAULT_STORE_ID}")
            if not price or price == "0":
                for attr, value in source.attrib.items():
                    if "data-price-value" in attr and value and value != "0":
                        price = value
                        break

            if not price or price == "0":
                # Check for .newPrice in rendered HTML
                price_text = response.css(".newPrice::text").get()
                if not price_text:
                    # Alternative for listings
                    price_text = response.css(".current-price::text").get()

                if price_text:
                    price = price_text.replace("€", "").replace(",", ".").strip()

            if price:
                try:
                    if float(price) > 0:
                        item["price"] = price
                except ValueError:
                    pass

            image = source.attrib.get("data-image-u-r-l")
            if image:
                item["image"] = response.urljoin(image)
            else:
                item["image"] = response.css('img[src*="/content/dam/oasitigre/products/"]::attr(src)').get()
                if item["image"]:
                    item["image"] = response.urljoin(item["image"])

            if not item.get("brand") and item.get("name") and "Consilia" in item["name"]:
                item["brand"] = "Consilia"

            if item.get("name"):
                yield item
        else:
            # Fallback to standard Schema.org extraction if available
            yield from self.parse_sd(response)

    def get_ref(self, url, response):
        match = re.search(r"-(\d+)\.html$", url)
        if match:
            return match.group(1)
        return super().get_ref(url, response)
