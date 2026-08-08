import scrapy
from products.items import Product

class PatelbrosUSSpider(scrapy.Spider):
    name = "patelbros_us"
    allowed_domains = ["gethomesome.com", "patelbros.com"]
    api_key = "A045608F-898F-44A7-A5FB-F54A7C1930E2"

    def start_requests(self):
        yield scrapy.Request(
            "https://user-api.gethomesome.com/locations",
            headers={
                "apikey": self.api_key,
                "referer": "https://shop.patelbros.com/",
                "origin": "https://shop.patelbros.com",
            },
            callback=self.parse_locations
        )

    def parse_locations(self, response):
        locations = response.json()
        for loc in locations:
            location_id = loc.get("uniqueName")
            if not location_id:
                continue

            # Skip auxiliary categories if any are specified as disabled/gift/express etc.
            # but we definitely want Online listings for actual products.
            if loc.get("name") in ["Giftcard", "Preorder", "Catering", "floral", "customcakes", "express", "ExpressCafe", "deli"]:
                continue

            # Extract price lists for this location
            pricelists = loc.get("priceLists", [])
            for pl in pricelists:
                pricelist_id = pl.get("uniqueName")
                if not pricelist_id:
                    continue

                yield scrapy.Request(
                    "https://user-api.gethomesome.com/product/list?listType=ui",
                    headers={
                        "apikey": self.api_key,
                        "location": location_id,
                        "pricelist": pricelist_id,
                        "referer": "https://shop.patelbros.com/",
                        "origin": "https://shop.patelbros.com",
                    },
                    callback=self.parse_products,
                    meta={
                        "location_name": loc.get("name"),
                        "pricelist_name": pl.get("name")
                    }
                )

    def parse_products(self, response):
        """
        Extracts product data from Homesome product list API.
        """
        data = response.json()
        products = data.get("products", [])
        location_name = response.meta.get("location_name")

        for prod in products:
            item = Product()
            item["ref"] = prod.get("name")  # In Homesome, 'name' field is usually the slug/id
            item["name"] = prod.get("displayName")
            item["price"] = prod.get("price")
            item["brand"] = prod.get("brand") or "Patel Brothers"
            item["proof_currency"] = "USD"
            item["brand_wikidata"] = "Q55641396"

            upc = prod.get("upc")
            if upc:
                item["gtin"] = upc

            item["website"] = f"https://shop.patelbros.com/product/{item['ref']}"

            main_image = prod.get("mainImage")
            if main_image:
                if main_image.startswith("http"):
                    item["image"] = main_image
                else:
                    item["image"] = f"https://s3.us-west-2.amazonaws.com/www.gethomesome.com/productimages_tn/{main_image}.jpg"

            item["extras"] = {
                "location": location_name,
                "pricelist": response.meta.get("pricelist_name"),
                "type": prod.get("type"),
                "subType": prod.get("subType")
            }

            yield item
