import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class VomarNLSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Vomar (Netherlands).
    Wikidata: Q3202837

    @url https://www.vomar.nl/producten/vers/fruit/aardbeien/716405
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "vomar_nl"
    allowed_domains = ["vomar.nl"]
    start_urls = ["https://www.vomar.nl/producten"]

    item_attributes = {
        "located_in_wikidata": "Q3202837",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3202837",
                "name": "Vomar",
            }
        },
    }

    rules = (
        # Product pages
        Rule(LinkExtractor(allow=r"/producten/.*/\d+$"), callback="parse_sd"),
        # Category pages
        Rule(LinkExtractor(allow=r"/producten(/.*)?$"), follow=True),
    )

    def iter_linked_data(self, response):
        # Fallback to standard LD-JSON if any (unlikely for Product based on observation)
        yield from super().iter_linked_data(response)

        # Bespoke HTML parsing
        name = response.css("h1::text").get()
        if name:
            name = name.strip()

            # Price extraction
            price_large = response.css(".price .large::text").get()
            price_small = response.css(".price .small::text").get()

            if price_large and price_small:
                price = f"{price_large.strip()}{price_small.strip()}".replace(",", ".")
            else:
                price = None

            # Image
            image = response.css(".image img::attr(src)").get()

            # Ref from URL
            ref_match = re.search(r"/(\d+)$", response.url)
            ref = ref_match.group(1) if ref_match else None

            # Unit/Weight
            unit = response.css("h1 + span::text").get()
            if unit:
                unit = " ".join(unit.split()).strip()

            # Brand extraction from name (best effort)
            brand = None
            brands = ["MELKAN", "G'WOON", "MARKANT", "BOON", "SUM & SAM", "KANIS & GUNNINK", "VOMAR"]
            for b in brands:
                if b in name.upper():
                    brand = b.title()
                    break

            if price:
                yield {
                    "@type": "Product",
                    "name": name,
                    "image": response.urljoin(image) if image else None,
                    "description": unit,
                    "sku": ref,
                    "brand": brand,
                    "offers": {
                        "@type": "Offer",
                        "price": price,
                        "priceCurrency": "EUR",
                        "availability": "https://schema.org/InStock",
                    },
                }

    def post_process_item(self, item, response, ld_data):
        if not item.get("ref") and (sku := item.get("sku")):
            item["ref"] = sku

        # Handle Superunie brands
        if brand := item.get("brand"):
            if isinstance(brand, str):
                if brand.upper() in ["MELKAN", "G'WOON", "MARKANT", "BOON", "SUM & SAM", "KANIS & GUNNINK"]:
                    item["brand_wikidata"] = "Q1702581"

        yield from super().post_process_item(item, response, ld_data)
