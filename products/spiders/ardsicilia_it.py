from scrapy import Spider
from scrapy.http import JsonRequest
from products.items import Product

class ArdsiciliaITSpider(Spider):
    """
    Spider for ARD Discount (Sicilia, Italy).
    Retailer website: https://www.arddiscount.it/
    The site is an Angular SPA that fetches product data from a private API.

    Sample output:
    {
        "name": "Croccantini Per Cane Adulto purams",
        "ref": "9546",
        "sku": "43390",
        "image": "https://portale-interattivo.s3.eu-central-1.amazonaws.com/campagna/813/thumb/67f387bcef293.jpg",
        "website": "https://www.arddiscount.it/offerta/9546",
        "offers": [
            {
                "@type": "Offer",
                "price": 9.99,
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        ],
        "description": "kg.10"
    }
    """
    name = "ardsicilia_it"
    allowed_domains = ["studiovatore.com", "arddiscount.it"]
    list_url = "https://api-ard-prd.studiovatore.com/api/product/products/list"
    detail_url = "https://api-ard-prd.studiovatore.com/api/pricelist/pricelistservices/listPublic"

    custom_settings = {
        "CONCURRENT_REQUESTS": 16,
        "DOWNLOAD_DELAY": 0.2,
    }

    def start_requests(self):
        yield JsonRequest(
            url=self.list_url,
            data={"limit": 100, "page": 1, "searchField": []},
            callback=self.parse
        )

    def parse(self, response):
        data = response.json()
        items = data.get("items", [])
        for item in items:
            service_id = item.get("id")
            if service_id:
                yield JsonRequest(
                    url=self.detail_url,
                    data={"serviceId": service_id, "showService": True},
                    callback=self.parse_product,
                    meta={"serviceId": service_id}
                )

        total_pages = data.get("totalPages", 0)
        current_page = data.get("page", 1)
        if current_page < total_pages:
            yield JsonRequest(
                url=self.list_url,
                data={"limit": 100, "page": current_page + 1, "searchField": []},
                callback=self.parse
            )

    def parse_product(self, response):
        data = response.json()
        items = data.get("items", [])
        if not items:
            return

        item_data = items[0]
        product_data = item_data.get("Product", {})
        if not product_data:
            return

        product = Product()

        name = product_data.get("name", "")
        abstract = product_data.get("abstract", "")
        if abstract:
            name = f"{name} {abstract}".strip()

        if not name:
            # Fallback to some placeholder if name is still empty
            name = "Prodotto senza nome"

        product["name"] = name
        product["ref"] = str(product_data.get("id"))
        product["sku"] = product_data.get("sku")
        product["image"] = product_data.get("imageUrl")
        product["description"] = product_data.get("description")

        # Base website URL construction
        slug = product_data.get("slug")
        if slug:
            product["website"] = f"https://www.arddiscount.it/offerta/{product['ref']}/{slug}"
        else:
            product["website"] = f"https://www.arddiscount.it/offerta/{product['ref']}"

        price = item_data.get("priceReductionFirst")
        if price:
            product["offers"] = [{
                "@type": "Offer",
                "price": float(price),
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock" if product_data.get("status") == "active" else "https://schema.org/OutOfStock"
            }]

        yield product
