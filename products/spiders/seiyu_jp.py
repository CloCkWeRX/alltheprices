import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SeiyuJPSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Seiyu (Japan) (Q1061908).
    Fix #11.

    Sample output:
    {
        "name": "【うれしいおトク】キリ＆スティック 3パック入り",
        "website": "https://netsuper.rakuten.co.jp/seiyu/item/3073781068474/",
        "image": "https://netsuper.r10s.jp/item/seiyu/74/3073781068474.jpg",
        "ref": "3073781068474",
        "sku": "3073781068474",
        "brand": "ベル ジャポン",
        "price": 389.0,
        "proof_currency": "JPY",
        "offers": [
            {
                "@type": "Offer",
                "price": 389,
                "priceCurrency": "JPY"
            }
        ],
        "located_in_wikidata": "Q1061908"
    }
    """

    name = "seiyu_jp"
    allowed_domains = ["netsuper.rakuten.co.jp"]
    sitemap_urls = ["https://netsuper.rakuten.co.jp/contents/sitemap.xml"]
    sitemap_rules = [(r"/seiyu/item/(\d+)/", "parse_sd")]

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

    def start_requests(self):
        """
        Request sitemaps via Scrapy-Playwright since they are Akamai protected.
        """
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        """
        Only use Playwright for matched product pages to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data):
        # Filter out empty, unhydrated, or dummy/template pages to prevent dirty records
        if not item.get("name") or not item.get("name").strip():
            self.logger.info(f"Skipping unhydrated or empty item: {response.url}")
            return

        item["located_in_wikidata"] = "Q1061908"

        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

                if item.get("price") and item.get("proof_currency"):
                    break

        if item.get("price") is not None:
            try:
                price_str = str(item["price"]).replace(",", ".").strip()
                item["price"] = float(price_str)
            except ValueError:
                pass

        if not item.get("proof_currency"):
            item["proof_currency"] = "JPY"

        # Correct relative image URLs or undefined strings
        if item.get("image") == "https:undefined":
            item["image"] = None

        # Capture unique ref/sku
        ref_match = re.search(r"/seiyu/item/(\d+)/", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)
            item["sku"] = ref_match.group(1)

        # Extract brand from ld_data if present
        brand_data = ld_data.get("brand")
        if brand_data:
            if isinstance(brand_data, dict):
                item["brand"] = brand_data.get("name")
            elif isinstance(brand_data, str):
                item["brand"] = brand_data

        yield item
