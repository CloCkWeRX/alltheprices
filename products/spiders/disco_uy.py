import re

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.items import Product
from products.user_agents import FIREFOX_LATEST


class DiscoUYSpider(CrawlSpider):
    name = "disco_uy"
    allowed_domains = ["disco.com.uy"]
    start_urls = ["https://www.disco.com.uy/"]
    user_agent = FIREFOX_LATEST

    rules = (
        Rule(LinkExtractor(allow=r"/products/category/")),
        Rule(LinkExtractor(allow=r"/product/.*/\d+$"), callback="parse_item"),
    )

    def parse_item(self, response):
        item = Product()

        name = response.css("h1.det-nom::text").get()
        if not name:
            return

        item["name"] = name.strip()
        item["brand"] = response.css(".det-marca::text").get("").strip()
        item["website"] = response.url

        ref_text = response.css(".det-ref::text").get("")
        ref_match = re.search(r"(\d+)", ref_text)
        if ref_match:
            item["ref"] = ref_match.group(1)
        else:
            item["ref"] = response.url.split("/")[-1]

        # Prices
        # Often there are multiple .product-prices if there's a discount.
        # The last one usually has the best price for all customers or specific groups.
        # Based on analysis, the first is original, second is discounted.
        price_elements = response.css(".det-precios .product-prices")
        if price_elements:
            target_price = price_elements[-1]
            price_val = target_price.css(".val::text").get()
            price_mon = target_price.css(".mon::text").get("")

            if price_val:
                item["price"] = float(price_val.replace(".", "").replace(",", "."))
                if "U$S" in price_mon:
                    item["proof_currency"] = "USD"
                else:
                    item["proof_currency"] = "UYU"

        # Image
        image = response.css(".splide__slide img::attr(src)").get()
        if image:
            item["image"] = response.urljoin(image)

        # GTIN from keywords meta
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            parts = [p.strip() for p in keywords.split(",")]
            # Usually the last part is the GTIN/EAN if it's numeric and long enough
            for part in reversed(parts):
                if part.isdigit() and len(part) >= 8:
                    item["gtin"] = part
                    break

        item["located_in_wikidata"] = "Q16636819"

        yield item
