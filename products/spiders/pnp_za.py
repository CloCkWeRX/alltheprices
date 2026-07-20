import json
import re
from typing import Generator, Union
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class PnpZASpider(SitemapSpider, StructuredDataSpider):
    """
    Pick n Pay South Africa spider.
    Fixes #487.
    Wikidata: Q7190735 (Pick n Pay)
    """

    name = "pnp_za"
    allowed_domains = ["pnp.co.za"]

    item_attributes = {
        "brand_wikidata": "Q7190735",
        "proof_currency": "ZAR",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7190735",
                "name": "Pick n Pay",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://www.pnp.co.za/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/p/(\d{12,18}_[A-Z0-9]+)$", "parse_product"),
    ]

    def start_requests(self) -> Generator[Request, None, None]:
        # Support passing a single/multiple start_urls for testing
        if hasattr(self, "start_urls") and self.start_urls:
            urls = [self.start_urls] if isinstance(self.start_urls, str) else self.start_urls
            for url in urls:
                match = re.search(r"/p/(\d{12,18}_[A-Z0-9]+)", url)
                if match:
                    product_code = match.group(1)
                    api_url = f"https://www.pnp.co.za/pnphybris/v2/pnp-spa/products/{product_code}?fields=DEFAULT,averageRating,images(FULL),classifications,manufacturer,numberOfReviews,categories(FULL),baseOptions,baseProduct,variantOptions,variantType,productDetailsDisplayInfoResponse,quantityType,brandSellerId&storeCode=WC21&scope=details&lang=en&curr=ZAR"
                else:
                    api_url = url

                yield Request(
                    url=api_url,
                    callback=self.parse_product,
                    headers={
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en;q=0.9",
                    }
                )
        else:
            yield from super().start_requests()

    def _parse_sitemap(self, response: Response) -> Generator[Union[Request, Product], None, None]:
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # Intercept product requests and fetch from their API using standard request
                match = re.search(r"/p/(\d{12,18}_[A-Z0-9]+)$", request_or_item.url)
                if match:
                    product_code = match.group(1)
                    api_url = f"https://www.pnp.co.za/pnphybris/v2/pnp-spa/products/{product_code}?fields=DEFAULT,averageRating,images(FULL),classifications,manufacturer,numberOfReviews,categories(FULL),baseOptions,baseProduct,variantOptions,variantType,productDetailsDisplayInfoResponse,quantityType,brandSellerId&storeCode=WC21&scope=details&lang=en&curr=ZAR"
                    request_or_item = request_or_item.replace(
                        url=api_url,
                        callback=self.parse_product,
                    )
                    # Let's set essential headers for the API request
                    request_or_item.headers.update({
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-US,en;q=0.9",
                    })
            yield request_or_item

    def parse_product(self, response: Response) -> Generator[Product, None, None]:
        """
        Parses the JSON response from the Pick n Pay product API.
        """
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON from {response.url}: {e}")
            return

        if not data or "name" not in data:
            return

        product_code = data.get("code")
        if not product_code:
            return

        product = Product()
        product["name"] = data.get("name")
        product["website"] = f"https://www.pnp.co.za/p/{product_code}"
        product["ref"] = str(product_code)
        product["sku"] = str(product_code)
        product["brand"] = data.get("brand") or data.get("manufacturer")
        product["description"] = data.get("description")

        # Image
        images = data.get("images", [])
        zoom_images = [img for img in images if img.get("format") == "zoom"]
        image_url = None
        if zoom_images:
            image_url = zoom_images[0].get("url")
        elif images:
            image_url = images[0].get("url")

        if image_url:
            product["image"] = response.urljoin(image_url)

        # Price
        price_data = data.get("price") or {}
        price_val = price_data.get("value")
        if price_val is not None:
            product["price"] = float(price_val)
            old_price = price_data.get("oldPrice")
            if old_price and float(old_price) > 0:
                product["price_is_discounted"] = True
                product["price_without_discount"] = float(old_price)

        # GTIN/barcode
        # Let's look inside classifications for unit_barcode or barcode
        for classification in data.get("classifications", []):
            for feature in classification.get("features", []):
                feature_name = feature.get("name", "").lower()
                if "barcode" in feature_name:
                    feature_values = feature.get("featureValues", [])
                    if feature_values:
                        barcode = feature_values[0].get("value")
                        if barcode:
                            product["gtin"] = str(barcode)
                            if len(barcode) == 12:
                                product["gtin12"] = str(barcode)
                            elif len(barcode) == 13:
                                product["gtin13"] = str(barcode)
                            break

        # Set default/extra properties
        product["proof_currency"] = "ZAR"
        product["brand_wikidata"] = "Q7190735"

        # Merge spider extras if any
        product["extras"] = self.item_attributes.get("extras", {}).copy()

        yield product
