import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AtbmarketUASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for ATB-Market (Ukraine) (Q4054103).
    Fix #478.
    """

    name = "atbmarket_ua"
    allowed_domains = ["atbmarket.com"]
    sitemap_urls = ["https://www.atbmarket.com/sitemap.xml"]
    sitemap_rules = [(r"/product/([^/]+)$", "parse_sd")]

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
        "located_in_wikidata": "Q4054103",
        "brand_wikidata": "Q4054103",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4054103",
                "name": "ATB-Market",
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
        Only use Playwright for product pages to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                request_or_item.meta["playwright_context_kwargs"] = {
                    "user_agent": FIREFOX_LATEST,
                }
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["located_in_wikidata"] = "Q4054103"
        item["brand_wikidata"] = "Q4054103"
        item["proof_currency"] = "UAH"

        if ld_data:
            # Try to pull standard currency/price from offers
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

        # Try to extract the true SKU/product ID from data-productid first, falling back to ld_data, url match or page text
        product_id = response.xpath("//@data-productid").get()
        if not product_id:
            product_id = response.xpath("//span[contains(@class, 'custom-tag__text')]//strong/text()").get()
        if not product_id and ld_data:
            product_id = ld_data.get("sku") or ld_data.get("mpn")

        if product_id:
            item["ref"] = str(product_id).strip()
            item["sku"] = str(product_id).strip()
        else:
            ref_match = re.search(r"/product/.*-([a-zA-Z0-9]+)$", response.url)
            if ref_match:
                item["ref"] = ref_match.group(1)
                item["sku"] = ref_match.group(1)

        # Make sure title is clean (remove decorative characters like ➤ or ★ from name if any)
        if item.get("name"):
            name = item["name"]
            # Clean leading/trailing symbols, e.g. "➤ ", " ★ АТБ Маркет"
            name = re.sub(r"^➤\s*", "", name)
            name = re.sub(r"★\s*АТБ\s*Маркет\s*$", "", name)
            item["name"] = name.strip()

        # Clean description too if it has trailing characters
        if item.get("description"):
            desc = item["description"]
            desc = re.sub(r"➡\s*АТБМаркеті\s*", "", desc)
            item["description"] = desc.strip()

        yield item
