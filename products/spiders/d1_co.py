import re
from typing import Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class D1COSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Tiendas D1 (Colombia).
    Extracts product data from window.__STATE__ JavaScript object.

    Sample output:
    {
        "brand": "HALLS",
        "located_in_wikidata": "Q43403418",
        "gtin": "7702011116262",
        "image": "https://d1tiendas.vtexassets.com/arquivos/ids/156942/12006852_1.jpg?v=638459428549500000",
        "name": "Halls Extra Strong 9 Und",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "price": 1900.0,
                "priceCurrency": "COP"
            }
        ],
        "ref": "12006852",
        "website": "https://www.d1.com.co/halls-extra-strong-9-und-12006852/p"
    }
    """

    name = "d1_co"
    allowed_domains = ["d1.com.co"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.d1.com.co/sitemap.xml"]
    sitemap_rules = [
        (r"/p$", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q43403418",
    }

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # Tiendas D1 uses window.__STATE__ to store product information.
        # It's inside a <template data-type="json" data-varname="__STATE__"><script>...</script></template>
        state_match = re.search(
            r'data-varname="__STATE__">.*?<script>(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        if not state_match:
            # Fallback for other VTEX versions
            state_match = re.search(
                r"window\.__STATE__\s*=\s*({.*?});", response.text, re.DOTALL
            )

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

            if (
                "items" in prod_data
                and isinstance(prod_data["items"], list)
                and len(prod_data["items"]) > 0
            ):
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
                                comm_offer_ref = seller_data.get("commertialOffer", {}).get(
                                    "id"
                                )
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
                                        offers.append(
                                            {
                                                "@type": "Offer",
                                                "price": float(price),
                                                "priceCurrency": "COP",
                                                "availability": availability,
                                            }
                                        )

            yield {
                "@context": "http://schema.org/",
                "@type": "Product",
                "name": product_name,
                "brand": {"@type": "Brand", "name": brand_name},
                "description": description,
                "image": images[0] if images else None,
                "sku": prod_data.get("productReference") or sku_data.get("itemId"),
                "gtin": sku_data.get("ean"),
                "offers": offers,
                "url": response.url,
            }

        except Exception as e:
            self.logger.error(f"Error parsing window.__STATE__ on {response.url}: {e}")

    def post_process_item(
        self, item: Product, response: Response, ld_data: dict, **kwargs
    ):
        if not item.get("ref") and ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        if brand := ld_data.get("brand"):
            if isinstance(brand, dict):
                item["brand"] = brand.get("name")
            else:
                item["brand"] = brand

        if gtin := ld_data.get("gtin"):
            item["gtin"] = gtin

        if description := ld_data.get("description"):
            item["description"] = description

        if item.get("name"):
            yield item
