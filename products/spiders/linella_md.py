import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LinellaMdSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Linella (Moldova).
    Fixes #298.
    Wikidata: Q61085990
    """

    name = "linella_md"
    allowed_domains = ["linella.md"]
    sitemap_urls = ["https://linella.md/sitemap.xml"]
    sitemap_rules = [
        (r"/catalog/.+/.+", "parse_product"),
    ]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q61085990",
                "name": "Linella",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("h1::text").get()
        if name:
            product["name"] = name.strip()

        # Price extraction
        price_text = response.css(".product__rht .price h2::text").get()
        if not price_text:
            price_text = response.css(".price-products-catalog-content__static::text").get()

        if price_text:
            try:
                # Remove any non-numeric characters except dot
                clean_price = re.sub(r"[^\d.]", "", price_text.strip())
                if clean_price:
                    product["price"] = float(clean_price)
            except ValueError:
                pass

        # Image extraction
        image = response.css(".product__lft .slider-for img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        # Reference extraction (Cod produs)
        ref = response.css(".product__rht .rht__block_2 p span::text").get()
        if ref:
            product["ref"] = ref.strip()
        else:
            # Fallback to slug from URL
            product["ref"] = response.url.split("/")[-1]

        yield from self.post_process_item(product, response, {})
