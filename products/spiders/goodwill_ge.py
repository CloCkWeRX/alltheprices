import json
import urllib.parse
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class GoodwillGESpider(Spider):
    """
    Spider for Goodwill Georgia.
    Wikidata: Q118799213

    Sample output structured data:
    {
        "name": "PICCOLO - Classic Chips 180g",
        "website": "https://www.goodwill.ge/shop/1/details/990/112634",
        "image": "https://static.goodwill.ge/Goodwill_files/9122035f-6eb4-46b3-8078-a3fdac4184ba_Thumb.jpg",
        "ref": "112634",
        "gtin": "8033196754350",
        "located_in_wikidata": "Q118799213",
        "price": 5.35,
        "proof_currency": "GEL"
    }
    """

    name = "goodwill_ge"
    allowed_domains = ["goodwill.ge", "api.goodwill.ge"]
    start_urls = ["https://www.goodwill.ge/shop/1-gudvili-digomi/965-"]
    user_agent = FIREFOX_LATEST

    # Use a limit of 100 products per request
    LIMIT = 100

    def parse(self, response):
        # Extract accessToken from "__NEXT_DATA__" in response text
        import re
        idx = response.text.find('id="__NEXT_DATA__"')
        token = None
        if idx != -1:
            try:
                start = response.text.find(">", idx) + 1
                end = response.text.find("</script>", start)
                data = json.loads(response.text[start:end])
                token = data.get("props", {}).get("pageProps", {}).get("accessToken")
            except Exception as e:
                self.logger.error(f"Error parsing __NEXT_DATA__: {e}")

        if not token:
            # Fallback regex search for "accessToken" in response text
            match = re.search(r'"accessToken":"([^"]+)"', response.text)
            if match:
                token = match.group(1)

        if not token:
            self.logger.error("Failed to retrieve accessToken. Stopping spider.")
            return

        self.logger.info(f"Retrieved accessToken: {token[:30]}...")

        # Request category list using the accessToken
        url = "https://api.goodwill.ge/v1/Categories?shopId=1"
        yield Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            callback=self.parse_categories,
            meta={"token": token},
        )

    def parse_categories(self, response):
        token = response.meta["token"]
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from Categories API response")
            return

        categories = data.get("categories", [])
        if not categories:
            self.logger.info("No categories returned.")
            return

        for cat in categories:
            cat_id = cat.get("id")
            if cat_id is not None:
                yield self.make_products_request(token, cat_id, offset=0)

    def make_products_request(self, token, cat_id, offset):
        # Goodwill API uses Products?shopId=1&categoryId={cat_id}&limit={LIMIT}&offset={offset}
        url = f"https://api.goodwill.ge/v1/Products?shopId=1&categoryId={cat_id}&limit={self.LIMIT}&offset={offset}"
        return Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            callback=self.parse_products,
            meta={"token": token, "cat_id": cat_id, "offset": offset},
        )

    def parse_products(self, response):
        token = response.meta["token"]
        cat_id = response.meta["cat_id"]
        offset = response.meta["offset"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from Products API response")
            return

        products = data.get("products", [])
        if not products:
            return

        for p in products:
            item = Product()
            item["name"] = p.get("name")
            item["price"] = p.get("price")
            item["proof_currency"] = "GEL"
            item["located_in_wikidata"] = "Q118799213"

            # Primary image
            image_url = p.get("imageUrl")
            if image_url:
                item["image"] = image_url

            # Unique references
            pid = p.get("id")
            if pid:
                item["ref"] = str(pid)
                # Form PDP website URL: e.g. https://www.goodwill.ge/shop/1/details/{cat_id}/{pid}
                item["website"] = f"https://www.goodwill.ge/shop/1/details/{cat_id}/{pid}"

            # GTIN/barcode
            barcode = p.get("barCode")
            if barcode:
                item["gtin"] = str(barcode)

            # Description
            description = p.get("description")
            if description:
                item["description"] = description

            yield item

        # Paginate to next page if returned products count matches LIMIT
        if len(products) >= self.LIMIT:
            next_offset = offset + self.LIMIT
            yield self.make_products_request(token, cat_id, next_offset)
