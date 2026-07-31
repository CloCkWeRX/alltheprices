import re
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

BRAND_WIKIDATA_MAPPING = {
    "フジパン": "Q11332062",
    "日清食品": "Q1375376",
    "東ハト": "Q3544976",
    "山芳製菓": "Q11467472",
    "湖池屋": "Q11612015",
    "プリマハム": "Q7243031",
    "カルビー": "Q2933860",
    "ブルボン": "Q11335272",
    "ミツウロコ": "Q11342621",
    "ASAHI": "Q720516",
    "アサヒ": "Q720516",
}


class BigaJPSpider(Spider):
    """
    Spider for Big-A (Japan) (Q11330804).
    Fix #437.

    Sample output:
    {
        "name": "ミツウロコ 四季の恵み天然水 2L",
        "website": "https://www.biga.co.jp/products/",
        "image": "https://www.biga.co.jp/wp/wp-content/uploads/2026/07/20260701_11.png",
        "ref": "14136",
        "sku": "14136",
        "brand": "ミツウロコ",
        "brand_wikidata": "Q11342621",
        "price": 63.72,
        "proof_currency": "JPY",
        "located_in_wikidata": "Q11330804"
    }
    """

    name = "biga_jp"
    allowed_domains = ["biga.co.jp"]
    start_urls = ["https://www.biga.co.jp/products/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    def parse(self, response):
        # We loop through all product list items
        for box in response.css("div.box.su-post"):
            # Get the unique reference from the post ID (e.g. su-post-12042)
            post_id = box.attrib.get("id", "")
            ref_match = re.search(r"su-post-(\d+)", post_id)
            if not ref_match:
                continue
            ref = ref_match.group(1)

            # Detail extraction
            slogan = box.css("div.item_detail p.slogan::text").get()
            slogan = slogan.strip() if slogan else ""

            brand_name = box.css("div.item_detail p.production::text").get()
            brand_name = brand_name.strip() if brand_name else ""

            item_title = box.css("div.item_detail p.item::text").get()
            item_title = item_title.strip() if item_title else ""

            quantity = box.css("div.item_detail p.quantity::text").get()
            quantity = quantity.strip() if quantity else ""

            # Name combination
            name_parts = []
            if brand_name:
                name_parts.append(brand_name)
            if item_title:
                name_parts.append(item_title)
            if quantity:
                name_parts.append(quantity)

            name = " ".join(name_parts)
            if not name:
                continue

            # Image extraction (the main product image)
            image_src = box.css("div.item_image img:not([src*='genkainichousen'])::attr(src)").get()
            if image_src:
                image_src = response.urljoin(image_src)

            # Price extraction (prefer tax included, fallback to excluded)
            price = None
            tax_included_text = box.css("p.tax_excluded span.tax_included::text").get()
            if tax_included_text:
                price_match = re.search(r"[\d\.]+", tax_included_text.replace(",", ""))
                if price_match:
                    price = float(price_match.group(0))

            if price is None:
                tax_excluded_text = "".join(box.css("p.tax_excluded::text").getall())
                price_match = re.search(r"[\d\.]+", tax_excluded_text.replace(",", ""))
                if price_match:
                    price = float(price_match.group(0))

            # Determine brand wikidata
            brand_wikidata = None
            if brand_name:
                normalized_brand = brand_name.upper()
                if normalized_brand in BRAND_WIKIDATA_MAPPING:
                    brand_wikidata = BRAND_WIKIDATA_MAPPING[normalized_brand]
                else:
                    for k, v in BRAND_WIKIDATA_MAPPING.items():
                        if k in normalized_brand or normalized_brand in k:
                            brand_wikidata = v
                            break

            # If no brand name is listed, default brand to Big-A
            final_brand = brand_name if brand_name else "Big-A"
            final_brand_wikidata = brand_wikidata if brand_name else "Q11330804"

            product = Product(
                name=name,
                website=response.url,
                ref=ref,
                sku=ref,
                image=image_src,
                brand=final_brand,
                brand_wikidata=final_brand_wikidata,
                price=price,
                proof_currency="JPY",
                located_in_wikidata="Q11330804",
            )

            # Setup extra seller details in extras
            product["extras"] = {
                "seller": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q11330804",
                    "name": "Big-A",
                }
            }
            if slogan:
                product["extras"]["slogan"] = slogan

            yield product
