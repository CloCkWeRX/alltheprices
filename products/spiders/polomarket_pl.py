import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class PolomarketPLSpider(SitemapSpider, StructuredDataSpider):
    """
    POLOmarket (Poland) spider.
    Fixes #335.
    Wikidata: Q11821937

    This site uses Nuxt 3 with a complex hydration state.
    We extract core metadata using regex from the script tag and HTML content.
    """

    name = "polomarket_pl"
    allowed_domains = ["polomarket.pl"]
    sitemap_urls = ["https://polomarket.pl/sitemap.xml"]
    sitemap_rules = [(r"/produkty/", "parse_product")]

    item_attributes = {
        "proof_currency": "PLN",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11821937",
                "name": "POLOmarket",
            }
        }
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Name from title
        title = response.xpath("//title/text()").get()
        if title:
            # Title format: "Category - Name | Sklepy POLOmarket"
            # Or sometimes just "Name | Sklepy POLOmarket"
            name_part = title.split(" | ")[0]
            if " - " in name_part:
                name = name_part.split(" - ", 1)[1]
            else:
                name = name_part
            product["name"] = name.strip()

        # Image and Reference from Nuxt script
        js_text = response.xpath('//script[contains(text(), "window.__NUXT__")]/text()').get()
        if js_text:
            photo_match = re.search(r'photo:"(.*?)"', js_text)
            if photo_match:
                product["image"] = photo_match.group(1).replace(r"\u002F", "/")

            number_match = re.search(r'number:"(.*?)"', js_text)
            if number_match:
                product["ref"] = number_match.group(1)

        # Price extraction from HTML
        main_price_whole = response.css(".price-main__actual::text").get()
        main_price_fraction = response.css(".price-main__actual sup::text").get()

        if main_price_whole and main_price_fraction:
            product["price"] = float(f"{main_price_whole.strip()}.{main_price_fraction.strip()}")

        reg_price_text = response.xpath("//span[contains(text(), 'Cena regularna:')]/text()").get()
        if reg_price_text:
            # Polish locale uses dots in these specific span texts for regular price on this site
            reg_price_match = re.search(r"Cena regularna:\s*(\d+[.,]\d+)", reg_price_text)
            if reg_price_match:
                product["price_without_discount"] = float(reg_price_match.group(1).replace(",", "."))
                product["price_is_discounted"] = True

        yield from self.post_process_item(product, response, {})
