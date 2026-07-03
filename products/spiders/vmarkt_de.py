import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class VmarktDESpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for V-Markt (Germany).
    Wikidata: Q1504903
    Fixes #266.
    """
    name = "vmarkt_de"
    allowed_domains = ["v-markt.de"]
    start_urls = ["https://www.v-markt.de/vorbestellservice"]

    item_attributes = {
        "located_in_wikidata": "Q1504903",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1504903",
                "name": "V-Markt",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    rules = (
        # Product pages
        Rule(LinkExtractor(allow=r"/p\d+$"), callback="parse_product"),
        # Category pages
        Rule(LinkExtractor(allow=r"/Vorbestellservice/.*")),
    )

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("h1.product-title::text").get()
        if name:
            product["name"] = name.strip()

        # Price extraction: "ab 32,00 €"
        price_raw = response.css("p.product-price::text").get()
        if price_raw:
            # Remove "ab", "€", whitespace, and change comma to dot
            price_clean = price_raw.replace("ab", "").replace("€", "").replace("\xa0", "").strip().replace(",", ".")
            try:
                product["price"] = float(price_clean)
            except ValueError:
                self.logger.warning(f"Could not parse price: {price_raw} from {response.url}")

        image = response.css("img.product-image::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        # Ref from data-pid in the form
        ref = response.css("form#product-detail-form::attr(data-pid)").get()
        if not ref:
            # Fallback to URL
            match = re.search(r"/p(\d+)$", response.url)
            if match:
                ref = match.group(1)

        if ref:
            product["ref"] = ref

        yield from self.post_process_item(product, response, {})
