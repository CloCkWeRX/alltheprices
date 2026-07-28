import json
import urllib.parse
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class AgrohubGESpider(Spider):
    """
    Spider for Agrohub Georgia.
    Wikidata: Q124035697

    Sample output structured data:
    {
        "name": "Ice cream vegan / Ben&Jerry / 465 gr",
        "website": "https://www.agrohub.ge/product/ice-cream-vegan-benjerry-465-gr-p23277",
        "image": "https://static.agrohub.lemon.do/Agrohub_files/b2f76039-5d38-40b8-a7a7-8645600b323d_Thumb.jpg",
        "ref": "23277",
        "gtin": "8711327626386",
        "located_in_wikidata": "Q124035697",
        "price": 33.9,
        "proof_currency": "GEL"
    }
    """

    name = "agrohub_ge"
    allowed_domains = ["agrohub.ge", "api.agrohub.ge"]
    start_urls = ["https://www.agrohub.ge/"]
    user_agent = FIREFOX_LATEST

    # Use a large limit to minimize paginated requests and fetch products quickly
    LIMIT = 100

    def parse(self, response):
        # We need to find the Set-Cookie containing agrohub-access_token or access cookies
        # Scrapy responses store cookies, but since Set-Cookie was in the raw response headers,
        # we can look through the Set-Cookie headers in the response.
        set_cookie_headers = response.headers.getlist("Set-Cookie")
        token = None
        for cookie_bytes in set_cookie_headers:
            cookie_str = cookie_bytes.decode("utf-8", errors="ignore")
            if "agrohub-access_token=" in cookie_str:
                try:
                    cookie_val = cookie_str.split("agrohub-access_token=")[1].split(";")[0]
                    decoded = urllib.parse.unquote(cookie_val)
                    cookie_json = json.loads(decoded)
                    token = cookie_json.get("token")
                    if token:
                        break
                except Exception:
                    continue

        if not token:
            self.logger.error("Could not extract agrohub-access_token from headers. Trying to parse from text/scripts...")
            # Fallback: search for "token":"..." in Next.js JSON or script contents
            import re
            match = re.search(r'"token":"([^"]+)"', response.text)
            if match:
                token = match.group(1)

        if not token:
            self.logger.error("Failed to retrieve token. Stopping spider.")
            return

        self.logger.info(f"Retrieved token: {token[:30]}...")

        # Now start fetching products paginated
        yield self.make_api_request(token, page=1)

    def make_api_request(self, token, page):
        url = f"https://api.agrohub.ge/v1/Products?Limit={self.LIMIT}&Page={page}"
        return Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            callback=self.parse_api_response,
            meta={"token": token, "page": page},
        )

    def parse_api_response(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON from API response")
            return

        products = data.get("products", [])
        if not products:
            self.logger.info("No more products returned by the API.")
            return

        for p in products:
            item = Product()
            item["name"] = p.get("name")
            item["price"] = p.get("price")
            item["proof_currency"] = "GEL"
            item["located_in_wikidata"] = "Q124035697"

            # Primary image
            image_url = p.get("imageUrl")
            if image_url:
                item["image"] = image_url

            # Unique references
            pid = p.get("id")
            if pid:
                item["ref"] = str(pid)
                # Form PDP website URL: e.g. https://www.agrohub.ge/product/slug-p<id>
                # The slug is derived from name. We can slugify it roughly to make a helpful link
                slug = p.get("name", "").lower()
                # replace non-alphanumeric with hyphen
                import re
                slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
                item["website"] = f"https://www.agrohub.ge/product/{slug}-p{pid}"

            # GTIN/barcode
            barcode = p.get("barCode")
            if barcode:
                item["gtin"] = str(barcode)

            # Description
            description = p.get("description") or p.get("miniDescription")
            if description:
                item["description"] = description

            yield item

        # Paginate to the next page
        next_page = response.meta["page"] + 1
        # Stop at some high upper-limit or let it stop when empty
        yield self.make_api_request(response.meta["token"], page=next_page)
