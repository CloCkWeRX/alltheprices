import os
import re
from urllib.parse import urlparse
import scrapy
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class VoiCHSpider(scrapy.Spider):
    """
    Spider for VOI Migros-Partner (Switzerland).
    Wikidata: Q680727 (Parent: Migros Genossenschafts-Bund)
    Fix #264.
    """

    name = "voi_ch"
    allowed_domains = ["voi-migrospartner.ch"]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    start_urls = [
        "https://www.voi-migrospartner.ch/de-ch/aktionen",
        "https://www.voi-migrospartner.ch/fr-ch/actions",
        "https://www.voi-migrospartner.ch/it-ch/promozioni",
    ]

    def parse(self, response):
        teasers = response.xpath("//voi-m-teaser")
        for teaser in teasers:
            name_text = teaser.xpath(".//h2/text()").get()
            if not name_text:
                continue
            name = name_text.strip()

            # Image & Ref extraction
            default_source = teaser.xpath(".//a-picture/@defaultsource").get() or teaser.xpath(".//a-picture/@defaultSource").get()
            image = None
            ref = None
            if default_source:
                image = response.urljoin(default_source)
                parsed_url = urlparse(default_source)
                filename = os.path.basename(parsed_url.path)
                ref_match = re.search(r"^(\d+)-", filename)
                if ref_match:
                    ref = ref_match.group(1)
                else:
                    ref = filename.split(".")[0]

            # Price extraction
            price_text = teaser.xpath('.//p[@class="price"]/text()').get()
            price = None
            if price_text:
                price = price_text.strip()

            # Original price (price_without_discount)
            original_price_text = teaser.xpath('.//p[@class="original-price"]/text()').get()
            price_without_discount = None
            if original_price_text:
                orig_match = re.search(r"(\d+(?:\.\d+)?)", original_price_text)
                if orig_match:
                    price_without_discount = orig_match.group(1)

            # Description/size
            sale_text = teaser.xpath('.//p[@class="sale-text"]/text()').get()
            description = None
            if sale_text:
                description = sale_text.strip()

            product = Product()
            product["name"] = name
            product["website"] = response.url
            product["description"] = description
            product["image"] = image
            product["ref"] = ref
            product["price"] = price
            product["price_is_discounted"] = True
            product["price_without_discount"] = price_without_discount
            product["proof_currency"] = "CHF"
            product["located_in_wikidata"] = "Q680727"

            yield product
