from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider

class IdealfoodbasketUSSpider(CrawlSpider, StructuredDataSpider):
    """
    Ideal Food Basket (United States) spider.
    https://www.idealfoodbaskets.com

    Storefront on Instacart:
    https://www.instacart.com/store/ideal-food-basket/storefront

    Wikidata: Q111908729

    Sample output structured data:
    {
        "name": "Welch's Passion Fruit",
        "website": "https://www.instacart.com/products/35551-welch-s-passion-fruit-59-fl-oz?retailerSlug=ideal-food-basket",
        "image": "https://d2lnr5mha7bycj.cloudfront.net/product-image/file/large_6d9e8b3a-5d3c-4b5c-8b5c-8b5c8b5c8b5c.png",
        "description": "Welch's Passion Fruit 59 fl oz",
        "brand": "Welch's",
        "offers": [
            {
                "@type": "Offer",
                "price": "3.99",
                "priceCurrency": "USD",
                "url": "https://www.instacart.com/products/35551-welch-s-passion-fruit-59-fl-oz?retailerSlug=ideal-food-basket",
                "availability": "https://schema.org/InStock"
            }
        ],
        "ref": "35551",
        "price": 3.99,
        "proof_currency": "USD",
        "located_in_wikidata": "Q111908729"
    }
    """

    name = "idealfoodbasket_us"
    allowed_domains = ["instacart.com"]
    start_urls = ["https://www.instacart.com/store/ideal-food-basket/storefront"]

    rules = (
        Rule(LinkExtractor(allow=(r"/products/(\d+)-",), restrict_xpaths=('//a[contains(@href, "retailerSlug=ideal-food-basket")]',)), callback="parse_sd"),
    )

    custom_settings = {
        "USER_AGENT": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q111908729"

        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

                if item.get("price") and item.get("proof_currency"):
                    break

        if item.get("price") is not None:
            try:
                item["price"] = float(str(item["price"]).replace(",", ".").strip())
            except ValueError:
                pass

        # Extract brand if it's a dict or missing
        if brand := ld_data.get("brand"):
            if isinstance(brand, dict):
                item["brand"] = brand.get("name")
            else:
                item["brand"] = brand

        # Use the ID from URL as ref if not found
        if not item.get("ref"):
            item["ref"] = self.get_ref(response.url, response)

        yield item
