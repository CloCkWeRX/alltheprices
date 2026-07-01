import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class PoieszNLSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Poiesz Supermarkten (Netherlands).
    Wikidata: Q2521700

    This site uses Snakeware Cloud. Product data is embedded in a hydration state
    within a script tag at the end of the page.

    @url https://webwinkel.poiesz-supermarkten.nl/boodschappen/producten/269017
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "poiesz_nl"
    allowed_domains = ["poiesz-supermarkten.nl"]
    start_urls = [
        "https://webwinkel.poiesz-supermarkten.nl/boodschappen",
        "https://www.poiesz-supermarkten.nl/spaarcadeaus",
    ]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2521700",
                "name": "Poiesz Supermarkten",
            }
        }
    }

    rules = (
        Rule(LinkExtractor(allow=r"/boodschappen/producten/\d+"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/spaarcadeaus/.*/.+"), callback="parse_sd"),
        Rule(LinkExtractor(allow=(r"/boodschappen/.*", r"/spaarcadeaus/.*")), follow=True),
    )

    convert_microdata = True

    def iter_linked_data(self, response):
        # Fallback to standard LD-JSON if any
        yield from super().iter_linked_data(response)

        # Bespoke Snakeware hydration state parsing for webwinkel
        scripts = response.xpath('//script[not(@src)]/text()').getall()
        data = None
        for script_text in scripts:
            if "ShallowReactive" in script_text and "Reactive" in script_text:
                try:
                    data = json.loads(script_text)
                    break
                except (json.JSONDecodeError, TypeError):
                    continue

        if data and isinstance(data, list):
            product_id_match = re.search(r"/producten/(\d+)", response.url)
            product_key = f"product-{product_id_match.group(1)}" if product_id_match else None

            try:
                p_idx = -1
                for i, x in enumerate(data):
                    if isinstance(x, dict):
                        if product_key and product_key in x:
                            p_idx = x[product_key]
                            if isinstance(p_idx, int) and p_idx != -1:
                                break

                if p_idx == -1:
                    for i, x in enumerate(data):
                        if isinstance(x, dict) and "name" in x and "price" in x and "ean" in x and "commercialText" in x:
                            if "alert-message" not in x:
                                p_idx = i
                                break

                if p_idx != -1 and 0 <= p_idx < len(data):
                    p = data[p_idx]
                    if isinstance(p, dict):

                        def resolve(idx):
                            if isinstance(idx, int) and 0 <= idx < len(data):
                                return data[idx]
                            return idx

                        name = resolve(p.get("name"))
                        price = resolve(p.get("price"))
                        image = resolve(p.get("image"))
                        brand = resolve(p.get("brandName"))
                        ean = resolve(p.get("ean"))

                        if name and price is not None:
                            yield {
                                "@type": "Product",
                                "name": name,
                                "image": image,
                                "brand": brand,
                                "sku": str(ean) if ean else None,
                                "offers": {
                                    "@type": "Offer",
                                    "price": price,
                                    "priceCurrency": "EUR",
                                    "availability": "https://schema.org/InStock",
                                },
                            }
            except Exception:
                self.logger.debug("Failed to parse Snakeware hydration state", exc_info=True)

        # Bespoke HTML parsing for spaarcadeaus
        if "/spaarcadeaus/" in response.url:
            name = response.css("h1.single-product__title::text").get()
            if name:
                image = response.css(".single-product__image img::attr(src)").get()
                sku = response.css(".single-product__number::text").re_first(r"(\d+)")
                spaar_info = " ".join(response.css(".spaaractie-zegels *::text").getall()).strip()
                spaar_info = re.sub(r"\s+", " ", spaar_info)

                yield {
                    "@type": "Product",
                    "name": name.strip(),
                    "image": response.urljoin(image) if image else None,
                    "sku": sku,
                    "offers": {
                        "@type": "Offer",
                        "price": 0,
                        "priceCurrency": "EUR",
                        "description": spaar_info if spaar_info else None,
                        "availability": "https://schema.org/InStock",
                    },
                }

    def post_process_item(self, item, response, ld_data):
        # Extract brand if missing (since parse_ld might miss it)
        if not item.get("brand") and (brand := ld_data.get("brand")):
            item["brand"] = brand

        if brand := item.get("brand"):
            if isinstance(brand, str):
                # Superunie brands
                if brand.upper() in ["MELKAN", "G'WOON", "MARKANT", "BOON", "SUM & SAM", "KANIS & GUNNINK"]:
                    item["brand_wikidata"] = "Q1702581"

        if not item.get("ref") and (sku := item.get("sku")):
            item["ref"] = sku

        yield from super().post_process_item(item, response, ld_data)
