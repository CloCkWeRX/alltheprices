import json
import re
from typing import Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class WoolworthsAUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Woolworths Supermarkets (Australia).
    Wikidata: Q3249145
    Fixes #484.
    """

    name = "woolworths_au"
    allowed_domains = ["woolworths.com.au"]
    sitemap_urls = [
        "https://www.woolworths.com.au/sitemap-products-1.xml",
        "https://www.woolworths.com.au/sitemap-products-2.xml",
        "https://www.woolworths.com.au/sitemap-products-3.xml",
        "https://www.woolworths.com.au/sitemap-products-4.xml",
    ]
    sitemap_rules = [
        (r"/shop/productdetails/(\d+)/", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q3249145",
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
        urls_arg = getattr(self, "urls", None) or getattr(self, "url", None)
        if urls_arg:
            urls = urls_arg.split(",") if isinstance(urls_arg, str) else [urls_arg]
            for url in urls:
                yield Request(
                    url.strip(),
                    callback=self.parse_sd,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod(
                                "wait_for_selector",
                                "script#__NEXT_DATA__",
                                state="attached",
                                timeout=10000,
                            ),
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

    def _parse_sitemap(self, response: Response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                if request_or_item.callback == self.parse_sd:
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod(
                            "wait_for_selector",
                            "script#__NEXT_DATA__",
                            state="attached",
                            timeout=10000,
                        ),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        next_data_script = response.xpath(
            '//script[@id="__NEXT_DATA__"]/text()'
        ).get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                page_props = data.get("props", {}).get("pageProps", {})
                pd_details = page_props.get("pdDetails") or {}
                pd_product = pd_details.get("Product") or {}
                pd_schema = page_props.get("pdSchema") or {}

                name = pd_product.get("Name") or pd_schema.get("name")
                sku = (
                    str(pd_product.get("StockCode"))
                    if pd_product.get("StockCode")
                    else pd_schema.get("sku")
                )
                if not sku:
                    sku = self.get_ref(response.url, response)

                price = (
                    pd_product.get("Price")
                    if pd_product.get("Price") is not None
                    else pd_schema.get("offers", {}).get("price")
                )

                brand = pd_product.get("Brand")
                if not brand and isinstance(pd_schema.get("brand"), dict):
                    brand = pd_schema.get("brand", {}).get("name")

                image = (
                    pd_product.get("LargeImageFile")
                    or pd_product.get("MediumImageFile")
                    or pd_schema.get("image")
                )
                gtin = pd_schema.get("gtin13") or pd_schema.get("gtin8")
                description = pd_product.get("Description") or pd_schema.get(
                    "description"
                )

                if name:
                    ld_item = {
                        "@type": "Product",
                        "name": name,
                        "sku": sku,
                        "description": description,
                        "image": image,
                        "gtin13": gtin,
                        "offers": {
                            "@type": "Offer",
                            "price": price,
                            "priceCurrency": "AUD",
                            "availability": "https://schema.org/InStock",
                            "url": response.url,
                        },
                    }
                    if brand:
                        ld_item["brand"] = {"@type": "Brand", "name": brand}

                    yield ld_item
                    return
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        yield from super().iter_linked_data(response)

    def post_process_item(self, item: Product, response: Response, ld_data: dict):
        if not item.get("ref"):
            item["ref"] = self.get_ref(response.url, response)
        if not item.get("proof_currency"):
            item["proof_currency"] = "AUD"
        if not item.get("gtin") and ld_data:
            gtin = ld_data.get("gtin13") or ld_data.get("gtin8")
            if gtin:
                item["gtin"] = str(gtin)
        if not item.get("price") and ld_data:
            offers = ld_data.get("offers")
            if isinstance(offers, dict) and offers.get("price") is not None:
                item["price"] = offers["price"]
        if not item.get("brand") and ld_data:
            brand_obj = ld_data.get("brand")
            if isinstance(brand_obj, dict) and brand_obj.get("name"):
                item["brand"] = brand_obj["name"]
            elif isinstance(brand_obj, str):
                item["brand"] = brand_obj
        yield item

    def get_ref(self, url: str, response: Response = None) -> str:
        match = re.search(r"/shop/productdetails/(\d+)/", url)
        if match:
            return match.group(1)
        return super().get_ref(url, response)
