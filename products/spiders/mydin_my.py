import json
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from products.items import Product
from products.user_agents import FIREFOX_LATEST


class MydinMYSpider(Spider):
    """
    Spider for Mydin (Malaysia).
    Wikidata: Q6947269

    Sample output structured data:
    {
        "name": "MYHOME GOBLET GLASS 6S 6.5OZ MY-6S-GB",
        "website": "https://www.mydin.my/product/myhome-goblet-glass-6s-6-5oz-my-6s-gb-15132355",
        "image": "https://mymgtbe.mydin.my/media/catalog/product/cache/ea23624dd3dd1d412743d9df44c33835/0/3/036be8741bc42de126ee8900deae20cd8a27a56bd0a461a537b2af77ee82f37b.jpeg",
        "ref": "15132355",
        "brand": "Myhome",
        "located_in_wikidata": "Q6947269",
        "price": 15.9,
        "proof_currency": "MYR"
    }
    """

    name = "mydin_my"
    allowed_domains = ["mydin.my", "mymgtbe.mydin.my"]
    user_agent = FIREFOX_LATEST

    item_attributes = {
        "located_in_wikidata": "Q6947269",
    }

    graphql_url = "https://mymgtbe.mydin.my/graphql"

    def start_requests(self) -> Iterable[Request]:
        yield self.make_graphql_request(page=1)

    def make_graphql_request(self, page: int) -> Request:
        query = """
        query GetProducts($pageSize: Int!, $currentPage: Int!) {
          products(search: "", pageSize: $pageSize, currentPage: $currentPage) {
            total_count
            items {
              sku
              name
              url_key
              description {
                html
              }
              image {
                url
              }
              price_range {
                minimum_price {
                  final_price {
                    value
                    currency
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "pageSize": 50,
            "currentPage": page,
        }
        payload = {
            "query": query,
            "variables": variables,
        }
        return Request(
            url=self.graphql_url,
            method="POST",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            callback=self.parse_products,
            cb_kwargs={"page": page},
        )

    def parse_products(self, response: Response, page: int) -> Iterable[Product | Request]:
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Error parsing JSON from Mydin GraphQL: {e}")
            return

        products_data = data.get("data", {}).get("products", {})
        items = products_data.get("items", [])
        total_count = products_data.get("total_count", 0)

        for item_data in items:
            sku = item_data.get("sku")
            if not sku:
                continue

            name = item_data.get("name")
            if not name:
                continue
            name = name.strip()

            url_key = item_data.get("url_key")
            website = f"https://www.mydin.my/product/{url_key}" if url_key else f"https://www.mydin.my/product/{sku}"

            description_data = item_data.get("description") or {}
            description = description_data.get("html")

            image_data = item_data.get("image") or {}
            image = image_data.get("url")

            price_range = item_data.get("price_range") or {}
            minimum_price = price_range.get("minimum_price") or {}
            final_price = minimum_price.get("final_price") or {}

            price = final_price.get("value")
            currency = final_price.get("currency") or "MYR"

            # Skip items with "Not For Sale" in name (often promo gifts/GWPs with zero price)
            if "not for sale" in name.lower() or "gwp" in name.lower():
                continue

            # Extract brand from the name prefix
            brand = None
            words = name.split()
            if words:
                first_word_upper = words[0].upper()
                if first_word_upper in ["DR", "SRI", "D/", "OLD", "KING", "RASA", "GAJAH", "DUTCH"] and len(words) > 1:
                    brand = f"{words[0]} {words[1]}".title()
                else:
                    brand = words[0].title()

            product = Product(
                name=name,
                website=website,
                description=description,
                image=image,
                ref=str(sku),
                brand=brand,
                price=price,
                proof_currency=currency,
                offers=[{
                    "@type": "Offer",
                    "priceCurrency": currency,
                    "price": price,
                    "availability": "https://schema.org/InStock",
                }],
                **self.item_attributes,
            )
            yield product

        # Paginate to next page if there's more data and we got a full page
        if items and (page * 50 < total_count):
            yield self.make_graphql_request(page=page + 1)
