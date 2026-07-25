import json
import re
from urllib.parse import quote
from scrapy import Request, Spider
from scrapy.http import Response
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class LacoopeencasaARSpider(Spider):
    """
    Spider for La Coope en Casa (Argentina), Cooperativa Obrera (Wikidata Q5167981).
    Utilizes public catalog and search REST APIs to fetch rich structured product data.

    Sample output:
    {
        "name": "QUESO CREMA BLANCO LA SERENISIMA CLÁSICO ORIGINAL 290grs",
        "image": "https://www.lacoopeencasa.coop/media/lcec/publico/articulos/e/0/8/e089932a3b1920faf5c84a65aad93f67",
        "website": "https://www.lacoopeencasa.coop/producto/queso-crema-blanco-la-serenisima-clasico-original-290grs/714580",
        "ref": "714580",
        "brand": "La Serenísima",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "ARS",
                "price": 6299.00,
                "availability": "https://schema.org/InStock"
            }
        ],
        "located_in_wikidata": "Q5167981"
    }
    """

    name = "lacoopeencasa_ar"
    allowed_domains = ["lacoopeencasa.coop", "api.lacoopeencasa.coop"]
    user_agent = FIREFOX_LATEST

    start_urls = ["https://api.lacoopeencasa.coop/api/categorias/listado"]

    item_attributes = {
        "located_in_wikidata": "Q5167981",  # Cooperativa Obrera
    }

    def parse(self, response: Response):
        try:
            data = json.loads(response.text)
            categories = data.get("datos", [])
            # Also seed with some common grocery keywords to ensure we capture most products
            keywords = ["leche", "queso", "crema", "aceite", "fideos", "arroz", "harina", "pan", "galletitas", "manteca", "yogur"]
            for keyword in keywords:
                yield self.make_search_request(keyword, offset=0)

            for cat in categories:
                desc = cat.get("descripcion")
                if desc:
                    yield self.make_search_request(desc, offset=0)
        except Exception as e:
            self.logger.error(f"Error parsing categories list: {e}")

    def make_search_request(self, query: str, offset: int) -> Request:
        # Encode query correctly
        encoded_query = quote(query)
        url = f"https://api.lacoopeencasa.coop/api/buscar/articulos?q={encoded_query}&offset={offset}&pedido=0"
        return Request(
            url,
            callback=self.parse_search_results,
            cb_kwargs={"query": query, "offset": offset}
        )

    def parse_search_results(self, response: Response, query: str, offset: int):
        try:
            data = json.loads(response.text)
            # If "estado" is 1, we found matches
            if data.get("estado") == 1 and data.get("datos"):
                items = data["datos"]
                for item_data in items:
                    ref = item_data.get("cod_interno")
                    if not ref:
                        continue

                    name = item_data.get("descripcion")
                    if name:
                        name = name.strip()

                    image = item_data.get("imagen")
                    brand = item_data.get("marca_desc")
                    if brand:
                        brand = brand.strip().title()

                    price_str = item_data.get("precio")
                    price = float(price_str) if price_str is not None else None

                    # Generate canonical website URL for the product
                    # e.g., https://www.lacoopeencasa.coop/producto/<slug>/<cod_interno>
                    slug = self.slugify(name or "")
                    website = f"https://www.lacoopeencasa.coop/producto/{slug}/{ref}"

                    product = Product(
                        name=name,
                        image=image,
                        website=website,
                        ref=ref,
                        brand=brand,
                        offers=[{
                            "@type": "Offer",
                            "priceCurrency": "ARS",
                            "price": price,
                            "availability": "https://schema.org/InStock",
                        }],
                        **self.item_attributes
                    )

                    yield product

                # Paginate if we received a full page of 12 items
                if len(items) >= 12:
                    yield self.make_search_request(query, offset + 12)
        except Exception as e:
            self.logger.error(f"Error parsing search results for query '{query}': {e}")

    def slugify(self, text: str) -> str:
        # Simple slugification matching La Coope en Casa style
        text = text.lower()
        # Replace non-alphanumeric characters with spaces, then spaces with dashes
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s-]+", "-", text).strip("-")
        return text
