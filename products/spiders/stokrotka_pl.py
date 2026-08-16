import re
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class StokrotkaPLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Stokrotka (Poland).
    Wikidata: Q9345945
    """

    name = "stokrotka_pl"
    allowed_domains = ["sklep.stokrotka.pl"]
    sitemap_urls = ["https://sklep.stokrotka.pl/sitemap.xml"]
    sitemap_rules = [
        (r"/produkt/.*\.html$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "located_in_wikidata": "Q9345945",
    }

    def iter_linked_data(self, response: Response):
        name = response.xpath(
            '//meta[@property="og:title"]/@content | //meta[@name="og:title"]/@content'
        ).get()
        if not name:
            name = response.xpath("//h1/text()").get()

        image = response.xpath(
            '//meta[@property="og:image"]/@content | //meta[@name="og:image"]/@content'
        ).get()
        if image and not image.startswith("http"):
            image = response.urljoin(image)

        description = response.xpath(
            '//meta[@property="og:description"]/@content | //meta[@name="og:description"]/@content'
        ).get()

        ref = None
        if image:
            ref_match = re.search(r"product-(\d+)", image)
            if ref_match:
                ref = ref_match.group(1)

        if not ref:
            slug = response.url.split("/")[-1].replace(".html", "")
            ref = slug

        if name:
            yield {
                "@type": "Product",
                "name": name.strip(),
                "sku": ref,
                "image": image,
                "description": description.strip() if description else None,
                "offers": {
                    "@type": "Offer",
                    "priceCurrency": "PLN",
                    "availability": "https://schema.org/InStock",
                },
            }

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        if item.get("name"):
            item["name"] = item["name"].strip()

        yield item
