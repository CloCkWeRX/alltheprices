import codecs
import re
from typing import Iterable

import chompjs
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class A101TRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for A101 (Turkey).
    Wikidata: Q6034496

    Sample output structured data:
    {
        "name": "Birşah Süt 200 ml",
        "website": "https://www.a101.com.tr/kapida/sut-urunleri-kahvaltilik/birsah-sut-200-ml_p-12002640",
        "image": "https://cdn2.a101.com.tr/dbmk89vnr/CALL/Image/get/s64937Ymdt_1024x1024.png",
        "ref": "12002640",
        "brand": "BİRŞAH",
        "located_in_wikidata": "Q6034496",
        "price": "4.50",
        "proof_currency": "TRY",
        "gtin13": "8699118010968"
    }
    """

    name = "a101_tr"
    allowed_domains = ["a101.com.tr"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.a101.com.tr/sitemap.xml"]
    sitemap_rules = [
        (r"_p-(\d+)$", "parse_sd"),
    ]

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Start with standard LD-JSON
        yield from super().iter_linked_data(response)

        # Supplement with Next.js hydration data for barcodes and potentially better pricing
        scripts = response.xpath('//script[contains(text(), "self.__next_f.push")]/text()').getall()
        for script in scripts:
            if "productDetail" not in script:
                continue

            match = re.search(r'self\.__next_f\.push\(\[\d+,"(.*?)"\]\)', script, re.DOTALL)
            if not match:
                continue

            try:
                inner_str = match.group(1)
                if ":" in inner_str:
                    inner_str = inner_str.split(":", 1)[1]

                decoded_str = codecs.decode(inner_str, "unicode_escape")
                data = chompjs.parse_js_object(decoded_str)

                product = self._find_product_detail(data)
                if product:
                    attr = product.get("attributes", {})
                    ld_item = {
                        "@type": "Product",
                        "name": attr.get("name"),
                        "brand": attr.get("brandLabel") or attr.get("brand"),
                        "sku": product.get("id"),
                        "image": [
                            img.get("url")
                            for img in product.get("images", [])
                            if img.get("imageType") == "product"
                        ],
                        "offers": {
                            "@type": "Offer",
                            "price": product.get("price", {}).get("discounted")
                            or product.get("price", {}).get("normal"),
                            "priceCurrency": "TRY",
                            "availability": "https://schema.org/InStock"
                            if product.get("isEnabled") or product.get("stock", 0) > 0
                            else "https://schema.org/OutOfStock",
                        },
                    }
                    if ld_item["offers"]["price"] is not None:
                        price = ld_item["offers"]["price"]
                        if isinstance(price, (int, float)):
                            # Check if it looks like cents (e.g. 450 for 4.50)
                            # But some e-com prices are large (e.g. 25199.00 for 25199.00)
                            # In my curl for e-com it was "price":25199 (as a number in LD-JSON or meta)
                            # Wait, in the hydration for e-com it might be different.
                            # In the Kapida one it was 450 for 4.50.
                            # Let's check the price string if available to be sure.
                            price_str = product.get("price", {}).get("discountedStr") or product.get("price", {}).get("normalStr")
                            if price_str and "," in price_str and "." not in price_str:
                                # Turkish format: 4,50 TL
                                ld_item["offers"]["price"] = price_str.replace("TL", "").replace("₺", "").replace(".", "").replace(",", ".").strip()
                            elif price_str and "." in price_str:
                                # 4.50 TL or 25.199,00 TL?
                                # Actually Turkish often uses . for thousands and , for decimals.
                                # "4.50 TL" in Kapida was actually 4.50.
                                # Let's trust the number if it's there and we can't be sure about cents.
                                pass

                            # If it's Kapida, it seems to be in cents.
                            if "kapida" in response.url and isinstance(price, int) and price > 100:
                                 ld_item["offers"]["price"] = f"{price / 100:.2f}"

                    if attr.get("barcode"):
                        ld_item["gtin"] = attr["barcode"]
                    elif attr.get("barcodes"):
                        ld_item["gtin"] = attr["barcodes"][0]
                    yield ld_item
            except Exception:
                continue

    def _find_product_detail(self, obj):
        if isinstance(obj, dict):
            if "productDetail" in obj:
                return obj["productDetail"]
            for v in obj.values():
                res = self._find_product_detail(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_product_detail(item)
                if res:
                    return res
        return None

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q6034496"

        if not item.get("ref"):
            # Extract ref from URL if missing (e.g. _p-12002640)
            match = re.search(r"_p-(\d+)$", response.url)
            if match:
                item["ref"] = match.group(1)

        # Promotion of price and currency if they are in offers
        if "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                price = offers.get("price")
                if price and price != "0":
                    item["price"] = str(price)

                currency = offers.get("priceCurrency")
                if currency:
                    item["proof_currency"] = currency

        if item.get("gtin"):
            gtin = str(item["gtin"])
            if len(gtin) == 13:
                item["gtin13"] = gtin
            elif len(gtin) == 12:
                item["gtin12"] = gtin
            elif len(gtin) == 14:
                item["gtin14"] = gtin
            elif len(gtin) == 8:
                item["gtin8"] = gtin

        # Meta tags often have the price too
        if not item.get("price") or item.get("price") == "0":
             if price := response.xpath('//meta[@name="product:price:amount"]/@content').get():
                 item["price"] = price
             if not item.get("proof_currency"):
                 item["proof_currency"] = response.xpath('//meta[@name="product:price:currency"]/@content').get()

        if not item.get("name"):
            item["name"] = response.xpath('//meta[@property="og:title"]/@content').get() or response.xpath('//title/text()').get()

        if not item.get("brand"):
            item["brand"] = response.xpath('//meta[@name="og:brand"]/@content').get()

        yield item
