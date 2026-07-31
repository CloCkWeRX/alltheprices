import re
from typing import Iterable
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AmetllerOrigenESSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Ametller Origen (Spain).
    Wikidata: Q20106290

    Sample output structured data:
    {
        "name": "Netejador WC aroma a lavanda Frosch 750ml",
        "website": "https://www.ametllerorigen.com/ca/netejador-wc-aroma-a-lavanda-frosch-750ml/3379.html",
        "image": "https://www.ametllerorigen.com/dw/image/v2/BLZV_PRD/on/demandware.static/-/Sites-mastercatalog_AMETLLER/default/dw58313f50/images/products/3379/3379_1.jpg?sw=800&fmt=webp&q=80",
        "ref": "3379",
        "brand": "Frosch",
        "located_in_wikidata": "Q20106290",
        "price": 3.50,
        "proof_currency": "EUR"
    }
    """

    name = "ametller_origen_es"
    allowed_domains = ["ametllerorigen.com"]

    sitemap_urls = ["https://www.ametllerorigen.com/sitemap.xml"]
    sitemap_rules = [
        (r"/([^/]+)/(\d+)\.html$", "parse_sd"),
    ]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    def start_requests(self):
        # We start with the sample product detail page using Scrapy-Playwright
        yield Request(
            "https://www.ametllerorigen.com/ca/pera-blanquilla-extra/11.html",
            callback=self.parse_sd,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 5000),
                ]
            },
        )
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # If matched as a product page, parse it with Playwright enabled
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.callback = self.parse_sd
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_timeout", 5000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def iter_linked_data(self, response) -> Iterable[dict]:
        pass

    def parse_sd(self, response):
        yield from self._extract_product(response)

    def _extract_product(self, response):
        # Name from H1 or meta og:title
        name = response.xpath("//h1/text()").get()
        if name:
            name = name.strip()

        if not name:
            name = response.xpath('//meta[@property="og:title"]/@content').get()
            if name:
                name = name.replace("| Ametller Origen", "").strip()

        if not name or "trobat aquesta pàgina" in name or "buscat per tot arreu" in name:
            return

        ref_match = re.search(r"/(\d+)\.html$", response.url)
        ref = ref_match.group(1) if ref_match else ""

        # Price extraction:
        # Avoid matching stylesheet or script text nodes.
        # Find elements containing "€" that are not style/script
        price = None
        for text in response.xpath("//body//*[not(self::script or self::style)][contains(text(), '€')]/text()").getall():
            text = text.strip()
            if "interessar" in text.lower() or "gratuït" in text.lower() or "lliurament" in text.lower() or "comandes" in text.lower():
                continue
            # Match "0,45€" or "3,50 €" or similar
            match = re.search(r"(\d+[,.]\d+)\s*€", text)
            if match:
                price = float(match.group(1).replace(",", "."))
                break

        # Image extraction:
        image = ""
        if ref:
            image = response.xpath(f"//img[contains(@src, '/images/products/{ref}/')]/@src").get()
        if not image:
            image = response.xpath("//img[contains(@src, '/images/products/')]/@src").get()
        if not image:
            image = response.xpath('//meta[@property="og:image"]/@content').get()

        # Origen/Description
        # Let's find "ORIGEN" text node and get the text node immediately following it, ignoring script/style
        description = ""
        origen_node = response.xpath("//body//*[not(self::script or self::style)][contains(text(), 'ORIGEN') or contains(text(), 'Origen')]/following::*[not(self::script or self::style)]/text()").getall()
        for t in origen_node:
            t = t.strip()
            if t and t != ":" and len(t) < 100:
                description = f"Origen: {t}"
                break

        # Brand guessing
        known_brands = ["Frosch", "Natulim", "Salustar", "Lavera", "Flopp", "Happy Bio", "Ecomimidu", "Ismax", "Ecodo", "Nandu Jubany", "Fratelli Colombo", "Lluc Crusellas"]
        brand = "Ametller Origen"
        for b in known_brands:
            if b.lower() in name.lower():
                brand = b
                break

        item = Product(
            name=name,
            website=response.url,
            ref=ref,
            image=image,
            price=price,
            proof_currency="EUR",
            brand=brand,
            description=description,
            located_in_wikidata="Q20106290",
        )
        yield item
