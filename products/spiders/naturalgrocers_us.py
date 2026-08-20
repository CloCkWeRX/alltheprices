import re
import scrapy
from scrapy import Request
from products.items import Product


class NaturalgrocersUSSpider(scrapy.Spider):
    """
    Spider for Natural Grocers (United States) (Q17146520).
    Fix #489.
    """

    name = "naturalgrocers_us"
    allowed_domains = [
        "naturalgrocers.com",
        "cdn4dd.com",
        "doordash-static.s3.amazonaws.com",
    ]
    start_urls = ["https://shop.naturalgrocers.com/convenience/store/48663903"]

    custom_settings = {
        "TWISTED_REACTOR": (
            "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
        ),
        "DOWNLOAD_HANDLERS": {
            "https": (
                "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
            ),
            "http": (
                "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
            ),
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 1.0,
    }

    item_attributes = {
        "located_in_wikidata": "Q17146520",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q17146520",
                "name": "Natural Grocers",
            }
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": False,
                },
            )

    def parse(self, response):
        # Extract and follow category links
        cat_links = response.xpath(
            '//a[contains(@href, "/category/")]/@href'
        ).getall()
        for link in set(cat_links):
            url = response.urljoin(link)
            yield Request(
                url,
                callback=self.parse_category,
                meta={
                    "playwright": True,
                    "playwright_include_page": False,
                },
            )

        # Also process products from home store page
        yield from self._extract_products(response)

    def parse_category(self, response):
        yield from self._extract_products(response)

    def _extract_products(self, response):
        """
        Extract product data embedded in Next.js hydration payload scripts.
        """
        scripts = response.xpath(
            '//script[contains(text(), "__next_f")]/text()'
        ).getall()
        raw_text = "\n".join(scripts) if scripts else response.text

        try:
            full_text = raw_text.encode("utf-8").decode("unicode_escape")
        except Exception:
            full_text = raw_text.replace(r'\"', '"')

        # Regex to locate item_data blocks
        item_matches = re.finditer(r'\"item_data\":\{(.*?)\}', full_text)

        seen_refs = set()

        for item_match in item_matches:
            start_pos = item_match.start()
            block = item_match.group(1)

            # Extract item_name
            name_m = re.search(r'\"item_name\":\"([^\"]+)\"', block)
            if not name_m:
                continue
            name = name_m.group(1)

            # Extract item_id / ref
            id_m = re.search(r'\"item_id\":\"(\d+)\"', block)
            ref = id_m.group(1) if id_m else None
            if not ref or ref in seen_refs:
                continue

            # Extract price
            price_m = re.search(r'\"unit_amount\":(\d+)', block)
            if not price_m:
                continue
            price = float(price_m.group(1)) / 100.0

            # Extract image from nearby context (preceding card block)
            context_start = max(0, start_pos - 600)
            card_context = full_text[context_start:start_pos]
            img_m = re.search(
                r'\"remote\":\{\"uri\":\"([^\"]+)\"', card_context
            )
            if not img_m:
                img_m = re.search(r'\"uri\":\"([^\"]+)\"', card_context)
            image_url = img_m.group(1) if img_m else None

            # Extract brand if "Natural Grocers" in name
            brand = None
            brand_wikidata = None
            if "natural grocers" in name.lower():
                brand = "Natural Grocers"
                brand_wikidata = "Q17146520"

            seen_refs.add(ref)

            p = Product()
            p["name"] = name
            p["ref"] = ref
            p["sku"] = ref
            p["price"] = price
            p["proof_currency"] = "USD"
            p["website"] = response.url
            if image_url:
                p["image"] = image_url
            if brand:
                p["brand"] = brand
            if brand_wikidata:
                p["brand_wikidata"] = brand_wikidata
            p["located_in_wikidata"] = "Q17146520"

            yield p
