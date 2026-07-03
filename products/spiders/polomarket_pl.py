import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider


class PolomarketPLSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Polomarket (Poland).
    Wikidata: Q11821937

    This site uses Nuxt.js but product data is primarily extracted from HTML
    due to complexity in parsing the hydration state.
    """

    name = "polomarket_pl"
    allowed_domains = ["polomarket.pl"]
    start_urls = ["https://www.polomarket.pl/"]

    item_attributes = {
        "brand_wikidata": "Q11821937",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11821937",
                "name": "Polomarket",
            }
        },
    }

    rules = (
        Rule(LinkExtractor(allow=r"/produkty/[^/]+$"), callback="parse_sd"),
        Rule(
            LinkExtractor(
                allow=(
                    r"/oferta-lojalnosciowa",
                    r"/gazetki",
                    r"/nasze-marki",
                )
            ),
            follow=True,
        ),
    )

    def iter_linked_data(self, response):
        # Fallback to standard LD-JSON if any
        yield from super().iter_linked_data(response)

        name = response.css("h1::text").get()
        if name:
            name = name.strip()

            # Primary price (often promo price)
            price_integer = response.css(".price-main__actual::text").get()
            price_decimal = response.css(".price-main__actual sup::text").get()

            price = None
            if price_integer:
                price = price_integer.strip()
                if price_decimal:
                    price += "." + price_decimal.strip()

            # Fallback to Regular price if main price not found or to keep as extra
            reg_price_text = response.xpath(
                '//span[contains(text(), "Cena regularna")]/text()'
            ).get()
            if not price and reg_price_text:
                m = re.search(r"(\d+\.\d+)", reg_price_text)
                if m:
                    price = m.group(1)

            image = response.css(".image-container img::attr(src)").get()

            yield {
                "@type": "Product",
                "name": name,
                "image": response.urljoin(image) if image else None,
                "offers": {
                    "@type": "Offer",
                    "price": price,
                    "priceCurrency": "PLN",
                    "availability": "https://schema.org/InStock",
                },
                "url": response.url,
            }

    def post_process_item(self, item, response, ld_data):
        if not item.get("ref"):
            # Use slug from URL as reference
            ref = response.url.split("/")[-1]
            item["ref"] = ref

        yield from super().post_process_item(item, response, ld_data)
