import json
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class KauflandDESpider(StructuredDataSpider):
    """
    Spider for Kaufland (Germany).
    Wikidata: Q685967
    Fixes #441.
    """
    name = "kaufland_de"
    allowed_domains = ["kaufland.de"]
    start_urls = [
        "https://filiale.kaufland.de/angebote/uebersicht.html",
        "https://filiale.kaufland.de/angebote/naechste-woche.html",
    ]

    item_attributes = {
        "located_in_wikidata": "Q685967",
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    def parse(self, response):
        html = response.text
        pos = 0
        seen_refs = set()

        while True:
            idx = html.find("window.SSR[", pos)
            if idx == -1:
                break
            eq_idx = html.find("=", idx)
            end_script = html.find("</script>", idx)
            if eq_idx == -1 or end_script == -1 or eq_idx > end_script:
                pos = idx + 10
                continue

            raw_json = html[eq_idx + 1:end_script].strip()
            if raw_json.endswith(";"):
                raw_json = raw_json[:-1].strip()

            try:
                obj = json.loads(raw_json)
                props = obj.get("props", {})
                offer_data = props.get("offerData")
                offers_list = []

                if isinstance(offer_data, list):
                    for cat in offer_data:
                        offers_list.extend(cat.get("offers", []))
                elif isinstance(offer_data, dict):
                    for cyc in offer_data.get("cycles", []):
                        for cat in cyc.get("categories", []):
                            offers_list.extend(cat.get("offers", []))

                for offer in offers_list:
                    item = self.parse_offer(offer, response)
                    if item and item.get("ref"):
                        if item["ref"] not in seen_refs:
                            seen_refs.add(item["ref"])
                            yield item
            except Exception as e:
                self.logger.debug(f"Error parsing window.SSR JSON: {e}")

            pos = end_script + 9

    def parse_offer(self, offer, response):
        product = Product()

        title = offer.get("title") or offer.get("detailTitle")
        if title:
            product["name"] = title.strip()

        detail_desc = offer.get("detailDescription")
        detail_action = offer.get("detailAction")
        unit = offer.get("unit")
        desc_parts = [p.strip() for p in [detail_desc, detail_action, unit] if p and p.strip()]
        if desc_parts:
            product["description"] = " - ".join(desc_parts)

        price = offer.get("price")
        if price is not None:
            try:
                product["price"] = float(price)
            except (ValueError, TypeError):
                pass

        old_price_str = offer.get("formattedOldPrice")
        if old_price_str:
            try:
                clean_old = old_price_str.replace(",", ".").strip()
                old_price = float(clean_old)
                if old_price > 0 and (product.get("price") is None or old_price > product["price"]):
                    product["price_without_discount"] = old_price
            except (ValueError, TypeError):
                pass

        image = offer.get("listImage")
        if not image and offer.get("detailImages"):
            image = offer.get("detailImages")[0]
        if image:
            product["image"] = image

        ref = offer.get("klNr") or offer.get("offerId")
        if ref:
            product["ref"] = str(ref)

        product["website"] = response.url

        product["offers"] = [{
            "@type": "Offer",
            "price": product.get("price"),
            "priceCurrency": "EUR",
        }]

        items = list(self.post_process_item(product, response, {}))
        return items[0] if items else product
