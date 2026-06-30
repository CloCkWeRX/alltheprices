import json
import re
from typing import Iterable

from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class NaturesbasketINSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Nature's Basket (India).
    Issue #256. Wikidata Q28174237.

    Sample output:
    {
        "brand_wikidata": "Q28174237",
        "image": "https://blaze-assets.webcdn.store/cdn-cgi/image/format=auto,quality=auto/nba/1332762.png",
        "name": "The Good Eggs Cage Free Brown Eggs (Premium)",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "price": 135.0,
                "priceCurrency": "INR"
            }
        ],
        "ref": "https://www.naturesbasket.co.in/product-detail?id=PRD9D6EDA7C23B1428EB95C515CCB5A0A4E",
        "website": "https://www.naturesbasket.co.in/product-detail?id=PRD9D6EDA7C23B1428EB95C515CCB5A0A4E"
    }
    """

    name = "naturesbasket_in"
    allowed_domains = ["naturesbasket.co.in"]
    sitemap_urls = ["https://www.naturesbasket.co.in/sitemap.xml"]
    sitemap_rules = [(r"/product-detail\?id=", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "brand_wikidata": "Q28174237",
    }

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Nature's Basket embeds JSON-LD inside Next.js hydration scripts.
        # They use self.__next_f.push calls with escaped string payloads.
        payloads = re.findall(
            r"self\.__next_f\.push\(\[1,\"(.*?)\"\]\)", response.text, re.DOTALL
        )
        for p in payloads:
            if "Product" in p:
                try:
                    # Decode JS string escaping
                    decoded_p = json.loads(f'"{p}"')

                    # Remove Next.js prefix (e.g., "5:")
                    if ":" in decoded_p[:5]:
                        decoded_p = decoded_p[decoded_p.find(":") + 1 :]

                    data = json.loads(decoded_p)

                    yield from self._walk_for_product(data)
                except:
                    pass

        yield from super().iter_linked_data(response)

    def _walk_for_product(self, obj):
        if isinstance(obj, dict):
            if obj.get("@type") == "Product":
                yield obj
            if "dangerouslySetInnerHTML" in obj:
                inner_html = obj["dangerouslySetInnerHTML"].get("__html")
                if inner_html:
                    try:
                        inner_data = json.loads(inner_html)
                        yield from self._walk_for_product(inner_data)
                    except:
                        pass
            for v in obj.values():
                yield from self._walk_for_product(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._walk_for_product(item)

    def post_process_item(self, item: Product, response, ld_data):
        # Fallback for price if JSON-LD offers it as null
        if item.get("offers"):
            for offer in item["offers"]:
                if not offer.get("price"):
                    # Look for priceInPaisa in the response text
                    price_match = re.search(r"priceInPaisa.*?(\d+)", response.text)
                    if price_match:
                        offer["price"] = float(price_match.group(1)) / 100

        yield item
