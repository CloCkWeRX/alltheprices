import codecs
import re
from typing import Iterable

import chompjs
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ArazAZSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Araz (Azerbaijan).
    Wikidata: Q97224746

    Sample output structured data:
    {
        "name": "Eti Popkek Patisserie Kakao 200 qr",
        "website": "https://www.arazmarket.az/az/products/eti-popkek-patisserie-kakao-200-qr-1",
        "image": "https://b7x9kq.arazmarket.az/storage/products/1000000542.png",
        "ref": "1000000542",
        "brand": "Eti",
        "located_in_wikidata": "Q97224746",
        "price": 3.0,
        "proof_currency": "AZN"
    }
    """

    name = "araz_az"
    allowed_domains = ["arazmarket.az"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.arazmarket.az/sitemap.xml"]
    sitemap_rules = [
        (r"/products/", "parse_sd"),
    ]

    def iter_linked_data(self, response) -> Iterable[dict]:
        yield from super().iter_linked_data(response)

        scripts = response.xpath(
            '//script[contains(text(), "self.__next_f.push")]/text()'
        ).getall()
        for script in scripts:
            for match in re.finditer(r"self\.__next_f\.push\((.*?)\)", script, re.DOTALL):
                try:
                    args = chompjs.parse_js_object(match.group(1))
                    if (
                        not isinstance(args, list)
                        or len(args) < 2
                        or not isinstance(args[1], str)
                    ):
                        continue

                    payload = args[1]
                    if '"product"' not in payload:
                        continue

                    if ":" in payload:
                        payload = payload.split(":", 1)[1]

                    decoded_str = codecs.decode(payload, "unicode_escape")
                    data = chompjs.parse_js_object(decoded_str)

                    product_data = self._find_product(data)
                    if product_data:
                        ld_item = {
                            "@type": "Product",
                            "name": product_data.get("title"),
                            "sku": product_data.get("barcode"),
                            "image": product_data.get("images"),
                            "offers": {
                                "@type": "Offer",
                                "price": product_data.get("discount_price")
                                or product_data.get("sales_price"),
                                "priceCurrency": "AZN",
                                "availability": "https://schema.org/InStock",
                            },
                        }

                        if title := product_data.get("title"):
                            # Brands are usually the first word in the title on this site
                            ld_item["brand"] = title.split(" ")[0]

                        yield ld_item
                except Exception:
                    continue

    def _find_product(self, obj):
        if isinstance(obj, dict):
            if (
                "product" in obj
                and isinstance(obj["product"], dict)
                and "barcode" in obj["product"]
            ):
                return obj["product"]
            for v in obj.values():
                res = self._find_product(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_product(item)
                if res:
                    return res
        return None

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q97224746"

        if "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                price = offers.get("price")
                if price:
                    try:
                        item["price"] = float(str(price).replace(",", "."))
                    except ValueError:
                        pass

                currency = offers.get("priceCurrency")
                if currency:
                    item["proof_currency"] = currency

        if not item.get("proof_currency"):
            item["proof_currency"] = "AZN"

        if not item.get("ref") and ld_data.get("sku"):
            item["ref"] = str(ld_data["sku"])

        if not item.get("name"):
            item["name"] = (
                response.xpath('//meta[@property="og:title"]/@content').get()
                or response.xpath("//title/text()").get()
            )

        yield item
