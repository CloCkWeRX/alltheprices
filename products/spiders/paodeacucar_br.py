import json
import re

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class PaodeacucarBRSpider(CrawlSpider, StructuredDataSpider):
    """
    Pão de Açúcar (Brazil) spider.
    Wikidata: Q3411543 (Pão de Açúcar brand), Q1541470 (GPA parent)

    Discovery via homepage categories and SKUs found in __NEXT_DATA__ on category pages.
    Extraction via Schema.org JSON-LD.
    """

    name = "paodeacucar_br"
    allowed_domains = ["paodeacucar.com"]
    start_urls = ["https://www.paodeacucar.com/"]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
            "Referer": "https://www.google.com/",
        },
    }

    rules = [
        # Categories and pagination
        Rule(
            LinkExtractor(allow=(r"/secoes/", r"/categoria/", r"/alimentos", r"/bebidas"), deny=r"/produto/"),
            callback="parse_category",
            follow=True,
        ),
        # Products found via links (if any)
        Rule(LinkExtractor(allow=r"/produto/\d+"), callback="parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q3411543",
        "extras": {
            "seller": {
                "@type": "Organization",
                "name": "Pão de Açúcar",
                "@id": "https://www.wikidata.org/wiki/Q3411543",
            }
        },
    }

    def parse_category(self, response):
        """
        Extract SKU IDs from __NEXT_DATA__ and construct product URLs.
        """
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data:
            # Simple regex to find all "skus":["ID",...] patterns
            skus = re.findall(r'"skus":\[([^\]]+)\]', next_data)
            for sku_list in skus:
                # Clean up and split IDs
                ids = sku_list.replace('"', "").split(",")
                for product_id in ids:
                    product_id = product_id.strip()
                    if product_id and product_id.isdigit():
                        yield Request(
                            f"https://www.paodeacucar.com/produto/{product_id}",
                            callback=self.parse_sd,
                        )

    def parse_start_url(self, response, **kwargs):
        # Bootstrap discovery from homepage
        next_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data:
            try:
                data = json.loads(next_data)
                categories = data.get("props", {}).get("initialProps", {}).get("categories", [])
                for cat in categories:
                    link = cat.get("link") or cat.get("uiLink")
                    if link:
                        yield Request(response.urljoin(link))
            except (json.JSONDecodeError, KeyError):
                pass
        return []

    def post_process_item(self, item: Product, response, ld_data):
        if not item.get("ref"):
            # Extract ref from URL: /produto/153808/banana-prata-800g
            match = re.search(r"/produto/(\d+)", response.url)
            if match:
                item["ref"] = match.group(1)

        if not item.get("ref") and item.get("sku"):
            item["ref"] = item.get("sku")

        # Ensure currency is BRL if price is present
        if item.get("price") and not item.get("proof_currency"):
            item["proof_currency"] = "BRL"

        # Image might be a list in JSON-LD
        if isinstance(item.get("image"), list) and item["image"]:
            item["image"] = item["image"][0]

        if item.get("name"):
            yield item
