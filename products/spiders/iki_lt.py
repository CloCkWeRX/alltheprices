import json
from typing import Iterable

from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class IkiLTSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for IKI (Lithuania) on lastmile.lt.
    Wikidata: Q1653981

    Sample output structured data:
    {
        "name": "Apkeptos banguotos bulvių lazdelės AVIKO ZIG ZAG, 750 g",
        "website": "https://www.lastmile.lt/chain/IKI/product/Apkeptos-banguotos-bulviu-lazdeles-AVIKO-ZIG-ZAG-750-g-12996",
        "image": "https://storage.googleapis.com/download/storage/v1/b/lastmile-ui/o/import%2Fphotos%2Fconverted%2Fproduct%2FCvKfTzV4TN5U8BTMF1Hl_1PkAtU4IUiOneKtF0Df4_CvKfTzV4TN5U8BTMF1Hl_webpConverter_1_big.webp?generation=1698231188714831&alt=media",
        "ref": "12996",
        "located_in_wikidata": "Q1653981",
        "price": 2.99,
        "proof_currency": "EUR"
    }
    """

    name = "iki_lt"
    allowed_domains = ["lastmile.lt"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.lastmile.lt/sitemap.xml"]
    sitemap_rules = [
        (r"/chain/IKI/product/[^/]+-(\d+)", "parse_sd"),
    ]

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Do not call super().iter_linked_data(response) as it has no Schema.org markup.

        # Extract next.js __NEXT_DATA__
        script_text = response.xpath(
            '//script[@id="__NEXT_DATA__"]/text()'
        ).get()
        if not script_text:
            return

        try:
            data = json.loads(script_text)
            product_slug = data.get("query", {}).get("product")
            queries = data.get("props", {}).get("pageProps", {}).get("dehydratedState", {}).get("queries", [])
            for q in queries:
                query_key = q.get("queryKey")
                if (
                    query_key
                    and isinstance(query_key, list)
                    and len(query_key) > 1
                    and query_key[0] == "product"
                    and (not product_slug or query_key[1] == product_slug)
                ):
                    state_data_list = q.get("state", {}).get("data", [])
                    if not state_data_list:
                        continue

                    p_data = state_data_list[0]
                    product = p_data.get("product")
                    if not product:
                        continue

                    # Extract name in Lithuanian, fallback to English or other languages
                    name_dict = product.get("name") or {}
                    name = name_dict.get("lt") or name_dict.get("en") or next(iter(name_dict.values()), None)

                    # Extract description
                    desc_dict = product.get("description") or {}
                    description = desc_dict.get("lt") or desc_dict.get("en") or next(iter(desc_dict.values()), None)

                    sku = product.get("erpCode") or product.get("id")

                    # Image URL
                    image = product.get("photoUrl") or product.get("thumbUrl")

                    # Price calculations
                    discount_price = p_data.get("discountPrice")
                    actual_price = product.get("actualPrice")

                    price_is_discounted = False
                    price_without_discount = None
                    if discount_price is not None:
                        price = float(discount_price)
                        price_without_discount = float(actual_price) if actual_price is not None else None
                        price_is_discounted = True
                    else:
                        price = float(actual_price) if actual_price is not None else None

                    yield {
                        "@type": "Product",
                        "name": name,
                        "description": description,
                        "image": image,
                        "sku": sku,
                        "offers": {
                            "@type": "Offer",
                            "price": price,
                            "priceCurrency": "EUR",
                            "price_is_discounted": price_is_discounted,
                            "price_without_discount": price_without_discount,
                            "availability": "https://schema.org/InStock" if product.get("isInStock") else "https://schema.org/OutOfStock",
                        }
                    }
                    # We only care about the main product query for this PDP
                    break
        except Exception:
            return

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q1653981"

        if "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                item["price"] = offers.get("price")
                item["proof_currency"] = offers.get("priceCurrency") or "EUR"
                item["price_is_discounted"] = offers.get("price_is_discounted", False)
                item["price_without_discount"] = offers.get("price_without_discount")

        if not item.get("proof_currency"):
            item["proof_currency"] = "EUR"

        if not item.get("ref") and ld_data.get("sku"):
            item["ref"] = str(ld_data["sku"])

        yield item
