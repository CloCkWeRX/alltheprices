import base64
import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.items import Product

class BrookshirebrothersUSSpider(SitemapSpider):
    """
    Brookshire Brothers (United States) spider.
    Wikidata: Q4975084

    Sample output structured data:
    {
        "extras": {
            "@source_uri": "https://production-us-1.noq-servers.net/api/v1/application/products/3e39bbd3-9786-4b18-a861-b0bf00cf0956"
        },
        "gtin": "4709",
        "image": "https://d13jicmd7uan86.cloudfront.net/2294e1ff-b8bc-4dc8-83c7-abfb0074172a",
        "located_in_wikidata": "Q4975084",
        "name": "Pepper, Serrano",
        "price": "2.24",
        "price_is_discounted": false,
        "price_without_discount": "2.24",
        "proof_currency": "USD",
        "ref": "3e39bbd3-9786-4b18-a861-b0bf00cf0956",
        "website": "https://shop.brookshirebrothers.com/online/store-74/shop/all?pid=3e39bbd3-9786-4b18-a861-b0bf00cf0956&productName=pepper"
    }
    """
    name = "brookshirebrothers_us"
    allowed_domains = ["brookshirebrothers.com", "noq-servers.net"]
    sitemap_urls = ["https://shop.brookshirebrothers.com/sitemap.xml"]
    sitemap_rules = [
        (r"pid=([a-f0-9\-]{36})", "parse_product_discovery"),
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Encoding": "gzip",
        },
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }

    def parse_product_discovery(self, response):
        pid_match = re.search(r"pid=([a-f0-9\-]{36})", response.url)
        if pid_match:
            pid = pid_match.group(1)
            api_url = f"https://production-us-1.noq-servers.net/api/v1/application/products/{pid}"
            yield Request(
                api_url,
                callback=self.parse_product,
                headers={
                    "x-app-environment": "browser",
                    "referer": "https://shop.brookshirebrothers.com/",
                    "origin": "https://shop.brookshirebrothers.com",
                },
                meta={"website": response.url},
            )

    def parse_product(self, response):
        import json
        data = json.loads(response.text)
        if data.get("HasErrors"):
            return

        result = data.get("Result")
        if not result:
            return

        product = Product()
        product["name"] = result.get("Name")
        product["ref"] = result.get("Id")
        product["website"] = response.meta.get("website")
        product["image"] = result.get("ImageUrl")
        product["price"] = str(result.get("Price"))
        product["price_without_discount"] = str(result.get("PriceRegular"))
        product["price_is_discounted"] = result.get("PriceRegular") != result.get("Price")
        product["proof_currency"] = "USD"
        product["located_in_wikidata"] = "Q4975084"

        if cd := result.get("Cd"):
            try:
                # Based on observation, Cd is base64 encoded and contains the GTIN/UPC
                decoded = base64.b64decode(cd).decode("utf-8")
                # GTIN is usually 12-14 digits, we can try to extract it
                # Example: MDAwNDUyODQ5MDEwMDE= -> 00045284901001
                if decoded.isdigit():
                    product["gtin"] = decoded
            except Exception:
                pass

        yield product
