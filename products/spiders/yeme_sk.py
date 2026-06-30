import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class YemeSKSpider(SitemapSpider, StructuredDataSpider):
    """
    Yeme (Slovakia) spider.
    Fixes #271.
    Wikidata: Q108757006

    Sample output:
    {
        "name": "Coca Cola zero 12x0,5l",
        "website": "https://www.yeme.sk/coca-cola-zero-12x0-5l-p63203",
        "image": "https://www.yeme.sk/data/images/products/63203/coca-cola-zero-12x0-5l-lqa4j_full.jpg",
        "ref": "63203",
        "brand": "Coca Cola",
        "located_in": "Česko",
        "price": 18.99,
        "price_without_discount": 19.08,
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q108757006",
                "name": "Yeme"
            }
        }
    }
    """

    name = "yeme_sk"
    allowed_domains = ["yeme.sk"]
    sitemap_urls = ["https://www.yeme.sk/sitemap.xml"]
    sitemap_rules = [(r"-p(\d+)$", "parse_product")]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q108757006",
                "name": "Yeme",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("h1.b-detail-info__title::text").get()
        if name:
            product["name"] = name.strip()

        image = response.css(".b-product-gallery__item img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        ref_match = re.search(r"-p(\d+)$", response.url)
        if ref_match:
            product["ref"] = ref_match.group(1)

        # More robust price extraction
        main_price_raw = response.xpath("//p[contains(@class, 'b-detail-info__price')]//span[contains(@class, 'btn__inner')]/text()[normalize-space()]").get()
        if main_price_raw:
            product["price"] = float(main_price_raw.strip().replace(",", "."))

        discount_price_raw = response.css(".b-detail-info__price .btn__discount::text").get()
        if discount_price_raw:
            product["price_without_discount"] = float(discount_price_raw.strip().replace(",", ".").replace("€", "").strip())
            product["price_is_discounted"] = True

        supplier = response.xpath("//p[contains(text(), 'Dodávateľ:')]/text()").get()
        if supplier:
            product["brand"] = supplier.replace("Dodávateľ:", "").strip()

        origin = response.xpath("//p[contains(text(), 'Krajina pôvodu:')]/text()").get()
        if origin:
            product["located_in"] = origin.replace("Krajina pôvodu:", "").strip()

        yield from self.post_process_item(product, response, {})
