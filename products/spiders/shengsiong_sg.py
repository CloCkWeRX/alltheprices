import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ShengsiongSGSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Sheng Siong (Singapore) (Q3481878).
    Fix #457.
    """

    name = "shengsiong_sg"
    allowed_domains = ["shengsiong.com.sg"]
    start_urls = ["https://shengsiong.com.sg/"]

    rules = (
        Rule(LinkExtractor(allow=r"/product/.*"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/category/.*")),
        Rule(LinkExtractor(allow=r"/[a-z0-9-]+/[a-z0-9-]+")),
    )

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
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
    }

    item_attributes = {
        "located_in_wikidata": "Q3481878",
    }

    def _make_request(self, rule_index, link):
        req = super()._make_request(rule_index, link)
        req.meta["playwright"] = True
        req.meta["playwright_context_kwargs"] = {
            "user_agent": FIREFOX_LATEST,
        }
        return req

    def start_requests(self):
        urls = None
        if hasattr(self, "urls") and self.urls:
            urls = self.urls
        elif hasattr(self, "url") and self.url:
            urls = self.url

        if urls:
            if isinstance(urls, str):
                urls_list = [u.strip() for u in urls.split(",") if u.strip()]
            else:
                urls_list = urls
            for url in urls_list:
                yield Request(
                    url,
                    callback=self.parse_sd,
                    meta={
                        "playwright": True,
                        "playwright_context_kwargs": {
                            "user_agent": FIREFOX_LATEST,
                        },
                    },
                )
            return

        for url in self.start_urls:
            yield Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_context_kwargs": {
                        "user_agent": FIREFOX_LATEST,
                    },
                },
            )

    def parse_start_url(self, response, **kwargs):
        return self._extract_links(response)

    def _extract_links(self, response):
        extractor = LinkExtractor(allow=r"/product/.*")
        for link in extractor.extract_links(response):
            yield Request(
                link.url,
                callback=self.parse_sd,
                meta={
                    "playwright": True,
                    "playwright_context_kwargs": {
                        "user_agent": FIREFOX_LATEST,
                    },
                },
            )

    def parse_sd(self, response):
        # Fallback parsing directly from client-rendered DOM when no Schema.org JSON-LD is available
        item = Product()
        item["located_in_wikidata"] = "Q3481878"
        item["website"] = response.url

        # SKU / Ref
        sku = response.xpath("//*[text()='SKU']/following-sibling::*[1]/text()").get()
        if not sku:
            sku = response.xpath("//*[contains(text(), 'SKU')]/text()").re_first(r"SKU\s*[:\s]*(\d+)")
        if sku:
            item["ref"] = sku.strip()
            item["sku"] = sku.strip()

        # Image
        image = response.xpath("//img[contains(@src, '/products/lg/')]/@src").get()
        if not image:
            image = response.xpath("//img[contains(@src, '/products/')]/@src").get()
        if image:
            item["image"] = response.urljoin(image)

        # In DOM layout: Brand name, Product title, Pack size, Price
        price_text = response.xpath("//*[contains(text(), '$')]/text()").get()
        if price_text:
            price_match = re.search(r"\$\s*([\d.]+)", price_text)
            if price_match:
                price_val = float(price_match.group(1))
                item["offers"] = [
                    {
                        "@type": "Offer",
                        "price": price_val,
                        "priceCurrency": "SGD",
                    }
                ]

        text_lines = response.xpath("//div[contains(@class, 'product')]//text() | //main//text() | //div[@id='app']//text()").getall()
        clean_lines = [t.strip() for t in text_lines if t.strip()]

        if "SKU" in clean_lines:
            sku_idx = clean_lines.index("SKU")
            if sku_idx + 1 < len(clean_lines) and not item.get("ref"):
                item["ref"] = clean_lines[sku_idx + 1]
                item["sku"] = clean_lines[sku_idx + 1]

            if "Origin" in clean_lines:
                orig_idx = clean_lines.index("Origin")
                if orig_idx + 1 < len(clean_lines):
                    item["description"] = f"Origin: {clean_lines[orig_idx + 1]}"

        # Parse name and brand if URL has slug
        url_match = re.search(r"/product/([^/]+)", response.url)
        if url_match:
            slug = url_match.group(1)
            name_guess = slug.replace("-", " ").title()
            item["name"] = name_guess

        for i, line in enumerate(clean_lines):
            if line.startswith("$") and i >= 2:
                if i >= 3 and not clean_lines[i-3].startswith("$") and clean_lines[i-3] not in ["Home", "Cart", "Log In", "Sign Up"]:
                    item["brand"] = clean_lines[i-3]
                    item["name"] = f"{clean_lines[i-2]} ({clean_lines[i-1]})"
                elif i >= 2:
                    item["name"] = f"{clean_lines[i-2]} ({clean_lines[i-1]})"
                break

        if item.get("ref") or item.get("name"):
            yield item
