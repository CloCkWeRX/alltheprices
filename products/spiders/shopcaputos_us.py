import scrapy
from products.items import Product

class ShopcaputosUSSpider(scrapy.Spider):
    name = "shopcaputos_us"
    allowed_domains = ["gethomesome.com", "shopcaputos.com"]
    api_key = "354788A1-4F4F-42DD-A480-D427BE8E5316"

    def start_requests(self):
        yield scrapy.Request(
            "https://user-api.gethomesome.com/locations",
            headers={
                "apikey": self.api_key,
                "referer": "https://shop.shopcaputos.com/",
                "origin": "https://shop.shopcaputos.com",
            },
            callback=self.parse_locations
        )

    def parse_locations(self, response):
        locations = response.json()
        for loc in locations:
            location_id = loc.get("uniqueName")
            if not location_id:
                continue

            if loc.get("name") == "Giftcard":
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
                        "referer": "https://shop.shopcaputos.com/",
                        "origin": "https://shop.shopcaputos.com",
                    },
                    callback=self.parse_products,
                    meta={
                        "location_name": loc.get("name"),
                        "pricelist_name": pl.get("name")
                    }
                )

    def parse_products(self, response):
        """
        Sample output:
        {
            "brand": "Johnsonville",
            "image": "https://s3.us-west-2.amazonaws.com/www.gethomesome.com/productimages_tn/00077782008166.jpg",
            "name": "Johnsonville Italian Mild Sausage 19 oz (538 g)",
            "price": 6.59,
            "ref": "00077782008166",
            "website": "https://shop.shopcaputos.com/product/00077782008166"
        }
        """
        data = response.json()
        products = data.get("products", [])
        location_name = response.meta.get("location_name")

        for prod in products:
            item = Product()
            item["ref"] = prod.get("name") # This 'name' field in API is actually the slug/id
            item["name"] = prod.get("displayName")
            item["price"] = prod.get("price")
            item["brand"] = prod.get("brand")

            upc = prod.get("upc")
            if upc:
                item["gtin"] = upc

            item["website"] = f"https://shop.shopcaputos.com/product/{item['ref']}"

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
