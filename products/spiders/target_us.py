import json
import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST


def find_nested_keys(obj, key):
    """
    Recursively find all occurrences of a key in a nested dict/list structure.
    """
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for v in obj.values():
            yield from find_nested_keys(v, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_nested_keys(item, key)


class TargetUSSpider(SitemapSpider):
    """
    Spider for Target (USA).
    Uses Playwright to render product pages and retrieve dynamic prices.

    Sample output:
    {
        "name": "Fishwife Tinned Seafood Co Albacore Tuna with Soy Ginger - 3.2oz",
        "website": "https://www.target.com/p/fishwife-tinned-seafood-co-albacore-tuna-with-soy-ginger-3-2oz/-/A-94998632",
        "ref": "94998632",
        "gtin": "850046148125",
        "brand": "Fishwife Tinned Seafood Co",
        "description": "Our albacore tuna is pole-and-line caught...",
        "image": "https://target.scene7.com/is/image/Target/GUEST_da8edfd4-9e77-4811-bd01-3c2fb3c3e76e",
        "price": "6.99",
        "proof_currency": "USD",
        "located_in_wikidata": "Q1046951"
    }
    """

    name = "target_us"
    allowed_domains = ["target.com"]

    sitemap_urls = [
        "https://www.target.com/pdp/sitemap_00-0001.xml.gz",
    ]

    sitemap_rules = [
        (r"/p/[^/]+/-/A-(\d+)", "parse_product"),
    ]

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
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }

    item_attributes = {
        "located_in_wikidata": "Q1046951",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1046951",
                "name": "Target",
            }
        },
    }

    def _parse_sitemap(self, response):
        """
        Only use Playwright for product pages to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Extract unique reference ID (SKU) from URL
        match = re.search(r"/A-(\d+)", response.url)
        if match:
            product["ref"] = match.group(1)
        else:
            product["ref"] = response.url

        # Extract name
        name = response.xpath("//h1[@data-test='product-title']/text()").get()
        if not name:
            name = response.xpath("//h1/text()").get()
        if name:
            product["name"] = name.strip()

        # Extract price (rendered dynamically by JavaScript)
        price_text = response.xpath("//span[@data-test='product-price']/text()").get()
        if not price_text:
            price_text = response.css("[data-test='product-price']::text").get()
        if not price_text:
            price_text = response.xpath("//*[contains(@data-test, 'product-price')]/text()").get()

        if price_text:
            price_match = re.search(r"\$?([\d.]+)", price_text)
            if price_match:
                product["price"] = price_match.group(1)
                product["proof_currency"] = "USD"

        # Parse NextJS hydration scripts to get high fidelity metadata
        scripts = response.xpath("//script/text()").getall()
        state_data = None
        for s in scripts:
            if "dehydratedState" in s:
                try:
                    state_data = json.loads(s)
                    break
                except Exception:
                    pass

        if state_data:
            # 1. Extract brand
            brand_data = next(find_nested_keys(state_data, "primary_brand"), None)
            if brand_data and isinstance(brand_data, dict):
                product["brand"] = brand_data.get("name")

            # 2. Extract GTIN / barcode
            barcode = next(find_nested_keys(state_data, "primary_barcode"), None)
            if barcode:
                product["gtin"] = str(barcode)

            # 3. Extract description
            desc_data = next(find_nested_keys(state_data, "product_description"), None)
            if desc_data and isinstance(desc_data, dict):
                desc_text = desc_data.get("downstream_description")
                if desc_text:
                    # Strip raw HTML tags from description if they exist
                    desc_text = re.sub(r"<[^>]+>", " ", desc_text)
                    product["description"] = " ".join(desc_text.split())

            # 4. Extract image
            image_info = next(find_nested_keys(state_data, "image_info"), None)
            if image_info and isinstance(image_info, dict):
                img_url = image_info.get("primary_image", {}).get("url")
                if img_url:
                    product["image"] = img_url

        # Fallback metadata if NextJS parsing failed or properties were absent
        if not product.get("description"):
            product["description"] = response.xpath("//meta[@name='description']/@content").get()
        if not product.get("image"):
            product["image"] = response.xpath("//meta[@property='og:image']/@content").get()

        product["located_in_wikidata"] = "Q1046951"

        yield product
