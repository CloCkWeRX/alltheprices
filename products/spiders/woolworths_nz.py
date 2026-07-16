import json
import re
from typing import Any, Dict, Generator, Union
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class WoolworthsNZSpider(SitemapSpider, StructuredDataSpider):
    """
    Woolworths New Zealand spider.
    Fixes #257.
    Wikidata: Q5176845 (Woolworths New Zealand / Countdown)
    """

    name = "woolworths_nz"
    allowed_domains = ["woolworths.co.nz"]

    item_attributes = {
        "brand_wikidata": "Q5176845",
        "proof_currency": "NZD",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5176845",
                "name": "Woolworths New Zealand",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    }

    sitemap_urls = [
        "https://www.woolworths.co.nz/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/shop/productdetails\?stockcode=(\d+)", "parse_product"),
    ]

    def start_requests(self) -> Generator[Request, None, None]:
        # Support passing a single/multiple start_urls for testing
        if hasattr(self, "start_urls") and self.start_urls:
            urls = [self.start_urls] if isinstance(self.start_urls, str) else self.start_urls
            for url in urls:
                match = re.search(r"stockcode=(\d+)", url)
                if match:
                    stockcode = match.group(1)
                    api_url = f"https://www.woolworths.co.nz/api/v1/products/{stockcode}"
                else:
                    api_url = url

                yield Request(
                    url=api_url,
                    callback=self.parse_product,
                    meta={
                        "playwright": True,
                        "playwright_browser": "firefox",
                        "playwright_include_body": True,
                    },
                    headers={
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en-AU;q=0.9,en;q=0.8",
                        "content-type": "application/json",
                        "x-requested-with": "OnlineShopping.WebApp",
                    }
                )
        else:
            yield from super().start_requests()

    def _parse_sitemap(self, response: Response) -> Generator[Union[Request, Product], None, None]:
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # Intercept product requests and fetch from their API using playwright
                match = re.search(r"stockcode=(\d+)", request_or_item.url)
                if match:
                    stockcode = match.group(1)
                    api_url = f"https://www.woolworths.co.nz/api/v1/products/{stockcode}"
                    request_or_item = request_or_item.replace(
                        url=api_url,
                        callback=self.parse_product,
                    )
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_browser"] = "firefox"
                    request_or_item.meta["playwright_include_body"] = True
                    # Let's set essential headers for the API request
                    request_or_item.headers.update({
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en-AU;q=0.9,en;q=0.8",
                        "content-type": "application/json",
                        "x-requested-with": "OnlineShopping.WebApp",
                    })
            yield request_or_item

    def parse_product(self, response: Response) -> Generator[Product, None, None]:
        """
        Parses the JSON response from the Woolworths New Zealand product API.
        """
        try:
            # Under Playwright, response.text might contain HTML wrapper (e.g. <html><body><pre>...</pre></body></html>)
            text = response.text
            if "<pre>" in text:
                match = re.search(r"<pre[^>]*>(.*?)</pre>", text, re.DOTALL)
                if match:
                    text = match.group(1)

            data = json.loads(text)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON from {response.url}: {e}")
            return

        if not data or "name" not in data:
            return

        # Extract stockcode (ref)
        ref = data.get("sku") or response.url.split("/")[-1]

        # Extract price
        price_data = data.get("price") or {}
        price = price_data.get("salePrice") or price_data.get("originalPrice")

        # Map to product
        product = Product()
        product["name"] = data.get("name")
        product["website"] = f"https://www.woolworths.co.nz/shop/productdetails?stockcode={ref}"
        product["ref"] = str(ref)
        product["sku"] = str(ref)
        product["brand"] = data.get("brand")
        product["description"] = data.get("description")

        # Image
        if data.get("images"):
            product["image"] = data["images"][0].get("big") or data["images"][0].get("small")
        elif data.get("bigImageUrl"):
            product["image"] = data.get("bigImageUrl")

        if price:
            product["price"] = float(price)
            if price_data.get("isSpecial"):
                product["price_is_discounted"] = True
                if price_data.get("originalPrice"):
                    product["price_without_discount"] = float(price_data["originalPrice"])

        # Set default/extra properties
        product["proof_currency"] = "NZD"
        product["brand_wikidata"] = "Q5176845"

        # Merge spider extras if any
        product["extras"] = self.item_attributes.get("extras", {}).copy()

        yield product
