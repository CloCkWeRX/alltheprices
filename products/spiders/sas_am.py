import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class SasAmSpider(SitemapSpider, StructuredDataSpider):
    """
    SAS Supermarket (Armenia) spider.
    Fixes #390.
    Wikidata: Q1345441 (SAS Group)

    Sample output:
    {
        "name": "Seaweed \"Чим Чим Суши Нори\" 10 sheets",
        "website": "https://www.sas.am/en/catalog/spicess/2412/",
        "image": "https://www.sas.am/upload/Sh/imageCache/341/862/8621822813256923.webp",
        "ref": "2412",
        "brand": "Чим Чим",
        "price": 2250.0,
        "currency": "AMD",
        "description": "Seaweed for sushi and rolls, 10pcs.",
        "extras": {
            "located_in_wikidata": "Q1345441"
        }
    }
    """

    name = "sas_am"
    allowed_domains = ["sas.am"]
    sitemap_urls = ["https://www.sas.am/sitemap.xml"]
    sitemap_rules = [(r"/en/catalog/.*/\d+/$", "parse_product")]

    item_attributes = {
        "located_in_wikidata": "Q1345441",
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css(".card__title::text").get()
        if name:
            product["name"] = name.strip()

        image = response.css(".card__gallery-view-img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        ref_match = re.search(r"/(\d+)/$", response.url)
        if ref_match:
            product["ref"] = ref_match.group(1)

        # Price extraction: "2&nbsp;250 <span class="price__currency">AMD</span>"
        price_text = "".join(response.css(".price__new .price__text ::text").getall())
        if price_text:
            # Replace non-breaking spaces and other whitespace
            price_clean = price_text.replace("\xa0", "").strip()
            price_digits = re.sub(r"[^\d.]", "", price_clean)
            if price_digits:
                product["price"] = float(price_digits)

        product["proof_currency"] = "AMD"

        brand = response.css(".card__brand-link::text").get()
        if brand:
            product["brand"] = brand.replace("brand", "").strip()
        else:
            # Fallback to details table
            brand_fallback = response.xpath("//div[div[contains(text(), 'Brand')]]/div[contains(@class, 'card__detail-item-value')]/text()").get()
            if brand_fallback:
                product["brand"] = brand_fallback.strip()

        description = response.css(".card__subtitle p::text").get()
        if description:
            product["description"] = description.strip()

        yield from self.post_process_item(product, response, {})
