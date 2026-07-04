import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LotussTHSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Lotus's (Thailand).
    Wikidata: Q2358897
    The site uses Next.js and product data is stored in __NEXT_DATA__ script tag.

    Sample output:
    {
        "name": "SENSODYNE HERBAL MULTI CARE 160 G",
        "website": "https://www.lotuss.com/en/product/sensodyne-herbal-multi-care-fluoride-toothpaste-160g-50812948",
        "image": "https://o2o-static.lotuss.com/products/86368/50812948.jpg",
        "ref": "50812948",
        "sku": "50812948",
        "brand": "SENSODYNE",
        "offers": [
            {
                "@type": "Offer",
                "price": 195.0,
                "priceCurrency": "THB",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2358897",
                "name": "Lotus's"
            }
        }
    }
    """

    name = "lotuss_th"
    allowed_domains = ["lotuss.com", "lotuss-ax.com"]
    sitemap_urls = [
        "https://phoenix.lotuss.com/public/sitemap/en/sitemap.xml",
        "https://phoenix.lotuss.com/public/sitemap/th/sitemap.xml",
    ]
    sitemap_rules = [(r"/product/", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2358897",
                "name": "Lotus's",
            }
        }
    }

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data:
            return

        try:
            data = json.loads(next_data)
            product = data.get("props", {}).get("pageProps", {}).get("productDetailSSR", {})
            if not product:
                # Try another path if it exists
                product = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("product", {}).get("detail", {})

            if product:
                yield self._map_product(product, response)
        except Exception as e:
            self.logger.error(f"Error parsing __NEXT_DATA__: {e}")

    def _map_product(self, product: dict, response: Response) -> dict:
        sku = product.get("sku")
        name = product.get("name")

        images = product.get("mediaGallery", [])
        image = images[0].get("url") if images else None

        price = product.get("finalPricePerUOW")

        brand_data = product.get("links", {}).get("brand", {})
        brand = brand_data.get("name")

        availability = "https://schema.org/InStock" if product.get("stockStatus") == "IN_STOCK" else "https://schema.org/OutOfStock"

        # Synthetic Schema.org Product
        ld_item = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "sku": sku,
            "image": image,
            "brand": brand,
            "offers": {
                "@type": "Offer",
                "price": price,
                "priceCurrency": "THB",
                "availability": availability,
            },
        }
        return ld_item
