import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class BonareaESSpider(SitemapSpider):
    """
    Spider for bonÀrea (Spain).

    Sample output:
    {
        "website": "https://www.bonarea-online.com/online/producto/cutter-smarcut-inox-110100-08-martor/05_5513",
        "name": "Cutter Smarcut Inox 110100.08 Martor",
        "price": "3.35",
        "proof_currency": "EUR",
        "image": "https://images.bonarea.com/05_5513_1.png",
        "ref": "05_5513",
        "located_in_wikidata": "Q11924743"
    }
    """
    name = "bonarea_es"
    allowed_domains = ["bonarea-online.com"]
    sitemap_urls = ["https://www.bonarea-online.com/sitemap.xml"]
    sitemap_rules = [
        (r"/online/product[eo]/.*?/(\d+_\d+)", "parse_item"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def parse_item(self, response):
        # Skip "Product not found" pages
        if "este producto no existe" in response.text.lower() or "aquest producte no existeix" in response.text.lower():
            return

        product = Product()
        product["website"] = response.url

        name = response.xpath("//h1[contains(@class, 'title')]/text()").get()
        if not name:
            name = response.xpath("//h1/text()").get()
        if name:
            product["name"] = name.strip()

        # Price extraction
        # Example: <span class="h2 bold">9,16 €/u</span>
        price_text = response.xpath("//div[contains(@class, 'content-price')]//span[contains(@class, 'h2')]/text()").get()
        if not price_text:
            # Fallback
            price_text = response.xpath("//span[contains(@class, 'price')]/text()").get()

        if price_text:
            # Extract digits and comma/dot
            match = re.search(r"([\d,.]+)", price_text)
            if match:
                price = match.group(1).replace(",", ".")
                product["price"] = price
                product["proof_currency"] = "EUR"

        # Image extraction
        # We saw images at https://images.bonarea.com/
        image = response.xpath('//img[contains(@src, "images.bonarea.com")]/@src').get()
        if not image:
            image = response.xpath('//img[contains(@data-src, "images.bonarea.com")]/@data-src').get()

        if image:
            # Strip query parameters if present to get the clean image
            image = image.split('?')[0]
            product["image"] = response.urljoin(image)

        # Ref extraction from URL
        match = re.search(r"/(\d+_\d+)$", response.url)
        if match:
            product["ref"] = match.group(1)

        product["located_in_wikidata"] = "Q11924743"

        yield product
