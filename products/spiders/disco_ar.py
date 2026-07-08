import re
from typing import Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class DiscoARSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Disco (Argentina).
    Extracts product data from window.__STATE__ JavaScript object.

    Sample output:
    {
        "brand": "Nolita",
        "located_in_wikidata": "Q6135978",
        "extras": {
            "@source_uri": "https://www.disco.com.ar/vino-blanco-nolita-chardonnay-pera-750-cc/p",
            "owner": {
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "@type": "Organization",
                "name": "Cencosud"
            }
        },
        "gtin": "7791540048371",
        "image": "https://jumboargentina.vtexassets.com/arquivos/ids/179173/Nolita-Chardonnay---Pera-Nolita-Chardonnay---Pera-bot-cc-750-1-8662.jpg?v=636383375815900000",
        "name": "Vino Blanco Nolita Chardonnay & Pera 750 Cc",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/OutOfStock",
                "price": 124.19,
                "priceCurrency": "ARS"
            }
        ],
        "ref": "7986",
        "website": "https://www.disco.com.ar/vino-blanco-nolita-chardonnay-pera-750-cc/p"
    }
    """

    name = "disco_ar"
    allowed_domains = ["disco.com.ar"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.disco.com.ar/sitemap.xml"]
    sitemap_rules = [
        (r"/p$", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q6135978",
        "extras": {
            "owner": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "name": "Cencosud",
            }
        },
    }

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # Disco Argentina uses window.__STATE__ to store product information.
        # It's inside a <template data-type="json" data-varname="__STATE__"><script>...</script></template>
        state_match = re.search(r'data-varname="__STATE__">.*?<script>(.*?)</script>', response.text, re.DOTALL)
        if not state_match:
            # Fallback for other VTEX versions
            state_match = re.search(r"window\.__STATE__\s*=\s*({.*?});", response.text, re.DOTALL)

        if not state_match:
            return

        try:
            data = chompjs.parse_js_object(state_match.group(1))

            # Look for Product entries in the state
            product_key = None
            for key in data:
                if key.startswith("Product:"):
                    product_key = key
                    break

            if not product_key:
                return

            prod_data = data[product_key]

            product_name = prod_data.get("productName")
            brand_name = prod_data.get("brand")
            description = prod_data.get("description")

            # Find the first SKU
            sku_data = {}
            images = []
            offers = []

            if "items" in prod_data and isinstance(prod_data["items"], list) and len(prod_data["items"]) > 0:
                sku_ref = prod_data["items"][0].get("id")
                if sku_ref and sku_ref in data:
                    sku_data = data[sku_ref]

                    # Images
                    if "images" in sku_data:
                        for img_ref in sku_data["images"]:
                            img_id = img_ref.get("id")
                            if img_id and img_id in data:
                                images.append(data[img_id].get("imageUrl"))

                    # Sellers/Offers
                    if "sellers" in sku_data:
                        for seller_ref in sku_data["sellers"]:
                            seller_id = seller_ref.get("id")
                            if seller_id and seller_id in data:
                                seller_data = data[seller_id]
                                comm_offer_ref = seller_data.get("commertialOffer", {}).get("id")
                                if comm_offer_ref and comm_offer_ref in data:
                                    offer_data = data[comm_offer_ref]
                                    price = offer_data.get("Price")
                                    avail_qty = offer_data.get("AvailableQuantity", 0)
                                    availability = (
                                        "https://schema.org/InStock"
                                        if avail_qty > 0
                                        else "https://schema.org/OutOfStock"
                                    )

                                    if price is not None:
                                        offers.append({
                                            "@type": "Offer",
                                            "price": float(price),
                                            "priceCurrency": "ARS",
                                            "availability": availability,
                                        })

            yield {
                "@context": "http://schema.org/",
                "@type": "Product",
                "name": product_name,
                "brand": {"@type": "Brand", "name": brand_name},
                "description": description,
                "image": images[0] if images else None,
                "sku": sku_data.get("itemId") or prod_data.get("productReference"),
                "gtin": sku_data.get("ean"),
                "offers": offers,
                "url": response.url,
            }

        except Exception as e:
            self.logger.error(f"Error parsing window.__STATE__ on {response.url}: {e}")

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        if not item.get("ref") and ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        if item.get("name"):
            yield item
