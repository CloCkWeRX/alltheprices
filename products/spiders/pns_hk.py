import re
from scrapy import Request
from scrapy_playwright.page import PageMethod
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class PnsHKSpider(SitemapSpider):
    """
    Spider for ParknShop (Hong Kong) (Q7138619).
    Fix #488.
    """

    name = "pns_hk"
    allowed_domains = ["pns.hk", "api.pns.hk"]
    sitemap_urls = ["https://www.pns.hk/sitemap_prd_zh_HK_01.xml"]
    sitemap_rules = [(r"/p/(BP_[0-9]+|[0-9]+)", "parse_product")]

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
    }

    item_attributes = {
        "located_in_wikidata": "Q7138619",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7138619",
                "name": "PARKnSHOP",
            }
        },
    }

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(
                    url,
                    callback=self.parse_product,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_context_kwargs": {
                            "user_agent": FIREFOX_LATEST,
                        },
                    },
                )
            return

        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
                headers={"User-Agent": FIREFOX_LATEST},
            )

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                request_or_item.meta["playwright_include_page"] = True
                request_or_item.meta["playwright_context_kwargs"] = {
                    "user_agent": FIREFOX_LATEST,
                }
                yield request_or_item
            else:
                yield request_or_item

    async def parse_product(self, response):
        page = response.meta.get("playwright_page")
        try:
            code_match = re.search(r"/p/(BP_[0-9]+|[0-9]+)", response.url)
            if not code_match:
                self.logger.warning(f"No code match in url: {response.url}")
                return

            code = code_match.group(1)

            if page:
                # Wait briefly for page script/session/tokens if needed
                await page.wait_for_timeout(2000)
                api_url = f"https://api.pns.hk/api/v2/pnshk/products/{code}?fields=FULL&lang=zh_HK&curr=HKD"
                data = await page.evaluate(
                    f"""async () => {{
                        try {{
                            const resp = await fetch('{api_url}');
                            if (resp.ok) {{
                                return await resp.json();
                            }} else {{
                                console.log('Fetch status:', resp.status);
                            }}
                        }} catch (e) {{
                            console.log('Fetch error:', e);
                        }}
                        return null;
                    }}"""
                )
            else:
                data = None

            self.logger.info(f"API data returned for {code}: {data is not None}")

            if not data:
                return

            name = data.get("name")
            if not name:
                return

            item = Product()
            item["name"] = name.strip()
            item["website"] = response.url
            item["ref"] = code
            item["sku"] = data.get("code") or code
            item["proof_currency"] = "HKD"

            price_info = data.get("price") or data.get("elabPrice") or {}
            if price_info.get("value") is not None:
                item["price"] = float(price_info["value"])

            # Brand extraction
            master_brand = data.get("masterBrand") or {}
            brand_name = master_brand.get("name") or data.get("brandName")
            if brand_name:
                item["brand"] = brand_name.strip()

            # Description
            desc = data.get("description") or data.get("shortDescription")
            if desc:
                # Clean basic HTML tags like <BR>
                clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                if clean_desc:
                    item["description"] = clean_desc

            # Primary image
            images = data.get("images") or data.get("regularProductFrontImages") or []
            primary_img = None
            for img in images:
                if img.get("format") in ("zoom", "product") and img.get("url"):
                    primary_img = img["url"]
                    break
            if not primary_img and images and images[0].get("url"):
                primary_img = images[0]["url"]

            if primary_img:
                if not primary_img.startswith("http"):
                    primary_img = f"https://medias.pns.hk{primary_img}"
                item["image"] = primary_img

            item["located_in_wikidata"] = "Q7138619"
            item["extras"] = {
                "seller": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q7138619",
                    "name": "PARKnSHOP",
                }
            }

            yield item
        finally:
            if page:
                await page.close()
