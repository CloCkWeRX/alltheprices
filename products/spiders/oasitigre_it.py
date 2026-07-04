import json
import scrapy
from products.items import Product

class OasitigreITSpider(scrapy.Spider):
    """
    Oasi Tigre (Italy) spider.
    Uses Doofinder API for product discovery and extraction.
    Wikidata: Q114567858 (Magazzini Gabrielli S.p.A. - parent)

    Sample output structured data:
    {
        "brand": "Consilia",
        "description": " | Tessuto testato dermatologicamente Veloce assorbimento Comfort elevato Speciale velino superiore 3d x18 Pezzi Assorbenza 2 su 5",
        "gtin": "8000965230155",
        "image": "https://www.oasitigre.it/content/dam/oasitigre/products/00/70/5/4/main/jcr:content/renditions/main-360x360.jpeg",
        "located_in": "Oasi Tigre",
        "name": "Consilia Saper Scegliere Assorbenti Ultra Anatomico 18 Pezzi",
        "price": 1.69,
        "product_code": "7054",
        "proof_currency": "EUR",
        "ref": "7054",
        "website": "https://www.oasitigre.it/prodotti/cartasanitariaassorbentieinfanzia/assorbentipannoliniadultieinfanzia/consiliasaperscegliereassorbentiultraanatomico18pezzi-7054.html"
    }
    """
    name = "oasitigre_it"
    allowed_domains = ["oasitigre.it", "doofinder.com"]

    # Doofinder search API
    search_url = "https://eu1-search.doofinder.com/6/45775f4f6633e3a77192e0993ccf9eb7/_search?query=&rpp=100"
    base_url = "https://www.oasitigre.it"

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "origin": "https://www.oasitigre.it",
            "referer": "https://www.oasitigre.it/",
        }
    }

    def start_requests(self):
        yield scrapy.Request(f"{self.search_url}&page=1", callback=self.parse)

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return

        results = data.get("results", [])

        for res in results:
            product = Product()
            product["name"] = res.get("title")
            product["brand"] = res.get("brand")

            link = res.get("link")
            if link:
                product["website"] = self.base_url + link

            image_url = res.get("imageURL")
            if image_url:
                product["image"] = self.base_url + image_url

            product["ref"] = res.get("id")
            product["product_code"] = res.get("productCode")

            barcodes = res.get("barcodes")
            if barcodes:
                # barcodes can be a comma-separated string
                if isinstance(barcodes, str):
                    product["gtin"] = barcodes.split(",")[0]
                elif isinstance(barcodes, list):
                    product["gtin"] = barcodes[0]

            product["description"] = res.get("description")

            # Categories
            categories = res.get("categories")
            if categories:
                product["extras"] = {"categories": categories}

            # Price - The API has store-specific prices.
            # We'll try to find any priceValueXXX field.
            price = None
            # Store 425 was used in the issue example
            if "priceValue425" in res:
                price = res["priceValue425"]
            else:
                # Fallback to the first available priceValueXXX
                for key, value in res.items():
                    if key.startswith("priceValue") and isinstance(value, (int, float)):
                        price = value
                        break

            if price:
                product["price"] = price
                product["proof_currency"] = "EUR"

            product["located_in"] = "Oasi Tigre"
            product["located_in_wikidata"] = "Q114567858"

            yield product

        # Pagination
        total = data.get("total")
        if total:
            # results per page is 100
            from urllib.parse import urlparse, parse_qs
            current_page = int(parse_qs(urlparse(response.url).query).get("page", [1])[0])
            if current_page * 100 < total:
                yield scrapy.Request(f"{self.search_url}&page={current_page + 1}", callback=self.parse)
