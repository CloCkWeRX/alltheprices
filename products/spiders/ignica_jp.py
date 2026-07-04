from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
import re

class IgnicaJPSpider(CrawlSpider, StructuredDataSpider):
    """
    ignica (Japan) spider.
    Fixes #301.
    Wikidata: Q21019840 (United Super Markets Holdings Inc.)
    """

    name = "ignica_jp"
    allowed_domains = ["od.ignica.com"]
    start_urls = ["https://od.ignica.com/categories"]

    rules = (
        Rule(LinkExtractor(allow=r"/categoryitems/")),
        Rule(LinkExtractor(allow=r"/item\?.*itemCode=\d+"), callback="parse_product"),
    )

    item_attributes = {
        "located_in_wikidata": "Q21019840",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q21019840",
                "name": "United Super Markets Holdings Inc.",
            }
        }
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Extraction from hidden inputs
        name = response.css('input[name="itemName"]::attr(value)').get()
        if not name:
            name = response.xpath("//meta[@property='og:title']/@content").get()
        if name:
            product["name"] = name.strip()

        ref = response.css('input[name="itemCode"]::attr(value)').get()
        if not ref:
            ref_match = re.search(r"itemCode=(\d+)", response.url)
            if ref_match:
                ref = ref_match.group(1)

        if ref:
            product["ref"] = ref
            if len(ref) == 13 and ref.isdigit():
                product["gtin13"] = ref

        # Price extraction
        # unitPrice seems to be tax excluded price
        # front_item_select-price-tax-included contains the tax included price like "(税込 ￥1,485)"
        tax_included_price_text = response.css(".front_item_select-price-tax-included::text").get()
        if tax_included_price_text:
            price_match = re.search(r"￥([\d,]+)", tax_included_price_text)
            if price_match:
                product["price"] = float(price_match.group(1).replace(",", ""))

        if not product.get("price"):
            price = response.css('input[name="unitPrice"]::attr(value)').get()
            if price:
                product["price"] = float(price)

        product["proof_currency"] = "JPY"

        image = response.xpath("//meta[@property='og:image']/@content").get()
        if not image:
            image = response.css(".slider-for img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        description = response.xpath("//meta[@name='description']/@content").get()
        if description:
            product["description"] = description.strip()

        # Try to find brand
        # In the sample it was above the name in the details section: <p>D&M</p>
        brand = response.css(".c-figure-content__data > p::text").get()
        if brand:
            product["brand"] = brand.strip()

        yield from self.post_process_item(product, response, {})
