import json
import re

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class PlazaveaPESpider(SitemapSpider, StructuredDataSpider):
    name = "plazavea_pe"
    allowed_domains = ["plazavea.com.pe"]
    user_agent = BROWSER_DEFAULT

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7203672",
                "name": "plazaVea",
            }
        }
    }

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": 120,
    }

    sitemap_urls = ["https://www.plazavea.com.pe/robots.txt"]
    sitemap_rules = [
        (r"https://www.plazavea.com.pe/[\w-]+/p", "parse_product"),
    ]

    def parse_product(self, response: Response):
        # First try standard structured data extraction
        yield from self.parse_sd(response)

        # Then try VTEX specific extraction
        vtex_item = self.extract_vtex_data(response)
        if vtex_item:
            yield vtex_item

    def extract_vtex_data(self, response: Response) -> Product | None:
        script_text = response.xpath('//script[contains(text(), "vtex.events.addData")]/text()').get()
        if not script_text:
            return None

        # Use re.DOTALL to handle multiline script content
        match = re.search(r"vtex\.events\.addData\((.*)\);", script_text, re.DOTALL)
        if not match:
            return None

        try:
            # Use chompjs for more robust JavaScript object parsing
            data = chompjs.parse_js_object(match.group(1))
            if data.get("pageCategory") != "Product":
                return None

            item = Product()
            item["name"] = data.get("productName")
            item["brand"] = data.get("productBrandName")
            item["ref"] = data.get("productReferenceId")
            item["website"] = response.url
            if eans := data.get("productEans"):
                item["gtin"] = eans[0]

            price = data.get("productPriceTo") or data.get("productPriceFrom")
            if price:
                item["offers"] = [
                    {
                        "@type": "Offer",
                        "price": float(price),
                        "priceCurrency": "PEN",
                        "availability": "https://schema.org/InStock",
                    }
                ]

            image = response.xpath('//img[@id="image-main"]/@src').get()
            if image:
                item["image"] = response.urljoin(image)

            return item
        except Exception:
            self.logger.warning("Failed to parse VTEX JSON data", exc_info=True)
            return None

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        # Ensure we don't yield items that aren't Products (e.g. BreadcrumbList from parse_sd)
        # unless they have a name which is a good indicator of a Product item in this context.
        if item.get("name"):
            yield item
