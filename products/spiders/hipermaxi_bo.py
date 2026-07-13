import codecs
import re
from typing import Iterable

import chompjs
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class HipermaxiBOSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Hipermaxi (Bolivia).
    Wikidata: Q81968262

    Sample output structured data:
    {
        "name": "Gaseosa Pepsi 2.5 L CBN",
        "website": "https://www.hipermaxi.com/santa-cruz/hipermaxi-roca-y-coronado/producto/342332/gaseosa-pepsi-25-l-cbn",
        "image": "https://hipermaxi.com/tienda-api/marketfile/ImageEcommerce?hashfile=f77118f_ea37_4853_807c_e87682ca7f0d.webp&co=5&size=400x400",
        "ref": "342332",
        "brand": "PEPSI",
        "located_in_wikidata": "Q81968262",
        "price": "12.50",
        "proof_currency": "BOB"
    }
    """

    name = "hipermaxi_bo"
    allowed_domains = ["hipermaxi.com"]
    start_urls = ["https://www.hipermaxi.com/"]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
    }

    rules = (
        # Categories
        Rule(LinkExtractor(allow=(r"/seccion/\d+",)), follow=True, process_request="use_playwright"),
        # Products
        Rule(LinkExtractor(allow=(r"/producto/\d+/",)), callback="parse_sd", process_request="use_playwright"),
    )

    def use_playwright(self, request, response):
        request.meta["playwright"] = True
        return request

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Try standard LD-JSON first
        yield from super().iter_linked_data(response)

        # Parse Next.js hydration scripts
        scripts = response.xpath('//script[contains(text(), "self.__next_f.push")]/text()').getall()
        for script in scripts:
            # We look for something that looks like product data
            if '"idProduct"' not in script:
                continue

            matches = re.findall(r'self\.__next_f\.push\(\[\d+,"(.*?)"\]\)', script, re.DOTALL)
            for inner_str in matches:
                try:
                    # Next.js often has a prefix like '1:' or 'b:'
                    if ":" in inner_str[:3]:
                        inner_str = inner_str.split(":", 1)[1]

                    decoded_str = codecs.decode(inner_str, "unicode_escape")
                    data = chompjs.parse_js_object(decoded_str)

                    product = self._find_product_detail(data)
                    if product:
                        ld_item = {
                            "@type": "Product",
                            "name": product.get("description"),
                            "brand": product.get("brand"),
                            "sku": str(product.get("idProduct")),
                            "image": [product.get("photoUrl")] if product.get("photoUrl") else [],
                            "offers": {
                                "@type": "Offer",
                                "price": product.get("price"),
                                "priceCurrency": "BOB",
                                "availability": "https://schema.org/InStock" if product.get("stock", 0) > 0 else "https://schema.org/OutOfStock",
                            },
                        }
                        yield ld_item
                except Exception:
                    continue

    def _find_product_detail(self, obj):
        if isinstance(obj, dict):
            if "idProduct" in obj and "description" in obj:
                return obj
            for v in obj.values():
                res = self._find_product_detail(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_product_detail(item)
                if res:
                    return res
        return None

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q81968262"

        if not item.get("ref"):
            # Extract ref from URL if missing (/producto/342332/...)
            match = re.search(r"/producto/(\d+)/", response.url)
            if match:
                item["ref"] = match.group(1)

        if "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                price = offers.get("price")
                if price:
                    item["price"] = str(price)

                currency = offers.get("priceCurrency")
                if currency:
                    item["proof_currency"] = currency

        if not item.get("name"):
            item["name"] = response.xpath('//h1/text()').get() or response.xpath('//meta[@property="og:title"]/@content').get()

        if item.get("name"):
            item["name"] = item["name"].strip()

        yield item
