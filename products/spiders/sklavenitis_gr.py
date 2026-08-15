import re
import json
from datetime import datetime
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class SklavenitisGRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Sklavenitis (Greece).
    Wikidata: Q7536037
    """

    name = "sklavenitis_gr"
    allowed_domains = ["sklavenitis.gr"]
    sitemap_urls = ["https://www.sklavenitis.gr/sitemap/Products/sitemap_index.xml"]
    sitemap_rules = [(r"/.*-[a-z0-9]+/$", "parse_product")]

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
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type in ["image", "font", "media"],
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q7536037",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7536037",
                "name": "Sklavenitis",
            }
        },
    }

    def start_requests(self):
        # Request home page using playwright first to initialize session/cookies if needed
        yield Request(
            "https://www.sklavenitis.gr/",
            callback=self.parse_home,
            meta={
                "playwright": True,
                "playwright_include_page": False,
            },
        )

    def parse_home(self, response):
        for url in self.sitemap_urls:
            yield Request(
                url,
                self._parse_sitemap,
                meta={
                    "playwright": True,
                    "playwright_include_page": False,
                },
            )

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                request_or_item.meta["playwright_include_page"] = False
                yield request_or_item
            else:
                yield request_or_item

    def parse_product(self, response: Response):
        item_id = None
        item_name = None
        item_brand = None
        price = None

        # Try extracting structured analytics data from dataLayer or AnalyticsTrackableDebug script
        for script in response.xpath('//script/text()').getall():
            if '"event": "view_item"' in script or "view_item" in script:
                m = re.search(
                    r'\{\s*"event":\s*"view_item".*?"ecommerce":\s*(\{.*?\})\s*\}\);',
                    script,
                    re.DOTALL,
                )
                if m:
                    try:
                        ecom_data = json.loads(m.group(1))
                        items_list = ecom_data.get("items", [])
                        if items_list:
                            first_item = items_list[0]
                            item_id = str(first_item.get("item_id") or "")
                            item_name = first_item.get("item_name")
                            item_brand = first_item.get("item_brand")
                            price_val = first_item.get("price")
                            if price_val is not None:
                                price = float(price_val)
                    except Exception:
                        pass

        # Fallback to HTML selectors for product attributes
        if not item_name:
            item_name = response.xpath("//h1//text()").get()
            if item_name:
                item_name = item_name.strip()

        # Image extraction
        image_url = response.xpath('//meta[@property="og:image"]/@content').get()
        if not image_url:
            image_url = response.xpath('//div[contains(@class, "product")]//img/@src').get()
        if not image_url:
            image_url = response.xpath('//img[contains(@src, "/Products/")]/@src').get()

        # Fallback to HTML selector for price if price is still None
        if price is None:
            # Selector for piece price e.g., '2,68 €' or '2.68 €'
            price_texts = response.xpath(
                '//*[contains(@class, "price")]//text()[contains(., "€")]'
            ).getall()
            for pt in price_texts:
                pt_clean = pt.strip()
                if pt_clean and not pt_clean.startswith("/"):
                    price_match = re.search(r"(\d+(?:[\.,]\d+)?)", pt_clean)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(",", "."))
                            break
                        except ValueError:
                            pass

        item = self.get_default_item(response)
        if item_name:
            item["name"] = item_name
        if item_brand:
            item["brand"] = item_brand
        if item_id:
            item["sku"] = item_id
            item["ref"] = item_id
        if image_url:
            item["image"] = response.urljoin(image_url)

        if price is not None:
            item["price"] = price
            item["proof_currency"] = "EUR"
            item["offers"] = [
                {
                    "@type": "Offer",
                    "price": price,
                    "priceCurrency": "EUR",
                    "availability": "https://schema.org/InStock",
                    "url": response.url,
                }
            ]

        yield item

    def get_default_item(self, response: Response) -> Product:
        return Product(
            website=response.url,
            date=datetime.now().isoformat(),
            located_in_wikidata="Q7536037",
        )
