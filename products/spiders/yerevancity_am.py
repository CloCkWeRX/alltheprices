import json
import hashlib
import time
import random
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class YerevancityAmSpider(Spider):
    """
    Spider for Yerevan City, the largest supermarket chain in Armenia.
    URL: https://www.yerevan-city.am/
    Issue: Fix #451

    Sample output structured data:
    {
        "name": "Peach (import) kg",
        "website": "https://www.yerevan-city.am/shop/product-details/26779",
        "image": "https://media.yerevan-city.am/api/Image/Resize/ProductPhoto/1046086.png",
        "ref": "26779",
        "located_in_wikidata": "Q874",
        "price": 6350.0,
        "price_is_discounted": false,
        "price_without_discount": null,
        "proof_currency": "AMD"
    }
    """

    name = "yerevancity_am"
    allowed_domains = ["yerevan-city.am", "apishopv2.yerevan-city.am"]
    start_urls = ["https://apishopv2.yerevan-city.am/api/Store/GetPublicSettings"]
    user_agent = FIREFOX_LATEST

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 4,
    }

    def start_requests(self):
        # Generate a deviceId like they do on the website: a random timestamp/hash or numeric string
        device_id = f"1785574052731{random.randint(100, 999)}abc"
        secret_str = "cdq`gORT`hv1g45'78sGGweqeU7641Bell||{asd}}}a((d)a*&^a%$a#@!5!T2QWacc1HeySenyorita" + device_id + "Web"
        key = hashlib.md5(secret_str.encode("utf-8")).hexdigest()

        register_url = "https://apishopv2.yerevan-city.am/api/Account/RegisterGuest"
        register_payload = {
            "deviceId": device_id,
            "osType": 3,
            "key": key
        }

        yield Request(
            register_url,
            method="POST",
            body=json.dumps(register_payload),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "ostype": "3"
            },
            callback=self.parse_registration,
            meta={"device_id": device_id}
        )

    def parse_registration(self, response):
        try:
            res_json = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse registration response: {e}")
            return

        if not res_json.get("success") or "data" not in res_json or "token" not in res_json["data"]:
            self.logger.error("Registration was not successful")
            return

        token = res_json["data"]["token"]
        self.logger.info(f"Registered guest session successfully. Token: {token[:20]}...")

        # Switch language to English (languageId: 1)
        lang_url = "https://apishopv2.yerevan-city.am/api/Account/UpdateLanguage/1?language=1"
        yield Request(
            lang_url,
            method="PUT",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "ostype": "3"
            },
            callback=self.parse_language_updated,
            meta={"token": token}
        )

    def parse_language_updated(self, response):
        token = response.meta["token"]
        self.logger.info("Language switched to English. Fetching parent categories...")

        # Get parent categories
        cat_url = "https://apishopv2.yerevan-city.am/api/Category/GetParentCategories"
        yield Request(
            cat_url,
            method="POST",
            body=b"{}",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "ostype": "3"
            },
            callback=self.parse_parent_categories,
            meta={"token": token}
        )

    def parse_parent_categories(self, response):
        token = response.meta["token"]
        try:
            res_json = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse parent categories: {e}")
            return

        parent_cats = res_json.get("data", {}).get("categories", [])
        if not parent_cats:
            self.logger.error("No parent categories found")
            return

        self.logger.info(f"Found {len(parent_cats)} parent categories.")
        for pcat in parent_cats:
            p_id = pcat.get("id")
            p_name = pcat.get("name")
            if not p_id:
                continue

            # Fetch all children categories recursively
            child_url = "https://apishopv2.yerevan-city.am/api/Category/GetAllChildren"
            yield Request(
                child_url,
                method="POST",
                body=json.dumps({"parentId": p_id}),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "ostype": "3"
                },
                callback=self.parse_category_children,
                meta={"token": token, "parent_name": p_name}
            )

    def parse_category_children(self, response):
        token = response.meta["token"]
        parent_name = response.meta["parent_name"]

        try:
            res_json = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse children categories for {parent_name}: {e}")
            return

        children = res_json.get("data", {}).get("children", [])
        leaf_category_ids = []

        def traverse_categories(cats):
            for cat in cats:
                cat_id = cat.get("id")
                if not cat_id:
                    continue
                if cat.get("children"):
                    traverse_categories(cat["children"])
                else:
                    leaf_category_ids.append(cat_id)

        traverse_categories(children)

        self.logger.info(f"Found {len(leaf_category_ids)} leaf categories under {parent_name}.")
        for cat_id in leaf_category_ids:
            yield self.make_products_request(token, cat_id, page=1)

    def make_products_request(self, token, cat_id, page):
        p_payload = {
            "categoryId": cat_id,
            "count": 50,
            "page": page,
            "priceFrom": None,
            "priceTo": None,
            "countries": [],
            "categories": [],
            "brands": [],
            "discount": False
        }

        url = "https://apishopv2.yerevan-city.am/api/Product/GetByCategory"
        return Request(
            url,
            method="POST",
            body=json.dumps(p_payload),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "ostype": "3"
            },
            callback=self.parse_products_page,
            meta={"token": token, "cat_id": cat_id, "page": page}
        )

    def parse_products_page(self, response):
        token = response.meta["token"]
        cat_id = response.meta["cat_id"]
        page = response.meta["page"]

        try:
            res_json = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse products page: {e}")
            return

        products_list = res_json.get("data", {}).get("list", []) or []
        if not products_list:
            return

        self.logger.info(f"Category {cat_id} Page {page}: processing {len(products_list)} products.")
        for p in products_list:
            pid = p.get("id")
            if not pid:
                continue

            item = Product()
            item["ref"] = str(pid)
            item["name"] = p.get("name")
            item["price"] = p.get("price")
            item["proof_currency"] = "AMD"
            item["located_in_wikidata"] = "Q874"  # Armenia
            item["website"] = f"https://www.yerevan-city.am/shop/product-details/{pid}"

            if p.get("photo"):
                item["image"] = p["photo"]

            # Manage discounts
            discounted_price = p.get("discountedPrice")
            if discounted_price and discounted_price > 0:
                item["price_is_discounted"] = True
                item["price_without_discount"] = p.get("price")
                item["price"] = discounted_price
            else:
                item["price_is_discounted"] = False

            if p.get("categoryName"):
                item["extras"] = {"category": p["categoryName"]}

            yield item

        # Paginate to next page if we got a full list of products
        if len(products_list) >= 50:
            yield self.make_products_request(token, cat_id, page + 1)
