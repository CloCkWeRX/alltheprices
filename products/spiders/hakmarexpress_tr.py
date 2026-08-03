import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class HakmarexpressTRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Hakmar Express (Turkey) (Q110454466).
    Fix #465.
    """

    name = "hakmarexpress_tr"
    allowed_domains = ["hakmarexpress.com.tr"]
    sitemap_urls = ["https://eticaret.s3.us-east-1.amazonaws.com/seo/sitemap.xml"]
    sitemap_rules = [(r"-p$", "parse_sd")]

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
    }

    item_attributes = {
        "located_in_wikidata": "Q110454466",
        "brand_wikidata": "Q110454466",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q110454466",
                "name": "Hakmar Express",
            }
        }
    }

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(
                    url,
                    callback=self.parse_sd,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "h1", timeout=20000),
                        ],
                        "playwright_context_kwargs": {
                            "user_agent": FIREFOX_LATEST,
                        }
                    }
                )
            return

        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
                headers={"User-Agent": FIREFOX_LATEST}
            )

    def _parse_sitemap(self, response):
        """
        Only use Playwright for actual product pages (matching sitemap_rules) to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # If matched as a product page, parse it with Playwright
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.callback = self.parse_sd
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_selector", "h1", timeout=20000),
                    ]
                    request_or_item.meta["playwright_context_kwargs"] = {
                        "user_agent": FIREFOX_LATEST,
                    }
                yield request_or_item
            else:
                yield request_or_item

    def parse_sd(self, response):
        # First, try standard structured data extraction
        items = list(super().parse_sd(response))
        if items:
            yield from items
            return

        # If no standard Product structured data was found, fallback to bespoke HTML extraction.
        item = Product(
            name=None,
            price=None,
            proof_currency=None,
            brand="Hakmar Express",
            description=None,
            image=None,
            ref=None,
            website=response.url,
        )
        yield from self.post_process_item(item, response, {})

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        item["located_in_wikidata"] = "Q110454466"
        item["brand_wikidata"] = "Q110454466"
        item["proof_currency"] = "TRY"

        # Extract/normalize the brand from meta/DOM
        # Brand label might be inside <span class="product-detail-meta-brand">
        brand = response.xpath("//span[contains(@class, 'product-detail-meta-brand')]/text()").get()
        if brand:
            item["brand"] = brand.strip()

        # Product Title/Name
        # If StructuredDataSpider didn't find the name or it's inaccurate, use H1
        title = response.xpath("//h1/text()").get()
        if title:
            item["name"] = title.strip()

        # Product ID / SKU / Ref
        # Format can be code at end, e.g. -1000268-p or matches code element
        code = response.xpath("//span[contains(@class, 'product-detail-meta-code')]/text()").get()
        if code:
            item["ref"] = code.strip()
            item["sku"] = code.strip()
        else:
            ref_match = re.search(r"-([a-zA-Z0-9]+)-p$", response.url)
            if ref_match:
                item["ref"] = ref_match.group(1)
                item["sku"] = ref_match.group(1)

        # Barcode
        # Can be inside col: Paket Ağırlığı: 1Barkod: 8690368943044
        # or inside <span class="text-brand"> following Barkod: or matches 13 digit number
        # We can extract it via XPath
        barcode = response.xpath("//p[contains(text(), 'Barkod:')]/span/text()").get()
        if not barcode:
            text_brand_spans = response.xpath("//span[contains(@class, 'text-brand')]/text()").getall()
            for val in text_brand_spans:
                val = val.strip()
                if val.isdigit() and len(val) >= 8 and len(val) <= 14:
                    barcode = val
                    break
        if barcode:
            item["gtin"] = barcode.strip()

        # Price
        # Parse from response element: <div class="product-price">265,00 ₺</div>
        price_text = response.xpath("//div[contains(@class, 'product-price')]/text()").get()
        if price_text:
            # Clean non-digit characters except comma, removing dots (thousands separators)
            price_cleaned = re.sub(r"[^\d,]", "", price_text).replace(",", ".").strip()
            if price_cleaned:
                try:
                    item["price"] = float(price_cleaned)
                except ValueError:
                    pass

        # Image
        # Src might be in img.p-detail-image
        image_src = response.xpath("//img[contains(@class, 'p-detail-image')]/@src").get()
        if image_src:
            item["image"] = response.urljoin(image_src)

        # Description
        # Standard description tab/text or default to name
        desc = response.xpath("//div[contains(@class, 'product-detail-description')]/text()").get()
        if not desc:
            desc_p = response.xpath("//div[contains(@class, 'ant-tabs-tabpane')]//p/text()").get()
            if desc_p:
                desc = desc_p
        if desc:
            item["description"] = desc.strip()

        yield item
