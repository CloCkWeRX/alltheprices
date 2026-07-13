from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MortonwilliamsUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Morton Williams (United States) spider.
    https://www.mortonwilliams.com/

    Wikidata: Q28227933

    Sample output structured data:
    {
        "name": "Actual Veggies Super Greens Veggie Burger",
        "website": "https://shop.mortonwilliams.com/store/morton-williams-supermarket/products/32676979-actual-veggies-super-greens-veggie-burger-4-pack",
        "image": "https://d2lnr5mha7bycj.cloudfront.net/product-image/file/large_e9054482-5836-4dff-8279-11efe6e04f6f.png",
        "description": "Actual Veggies Super Greens Veggie Burger with Broccoli, Kale, White Bean & Spinach 4 - 3 oz Patties",
        "brand": "Actual Veggies",
        "offers": [
            {
                "@type": "Offer",
                "price": "9.49",
                "priceCurrency": "USD",
                "url": "https://shop.mortonwilliams.com/store/morton-williams-supermarket/products/32676979-actual-veggies-super-greens-veggie-burger-4-pack",
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock"
            }
        ],
        "ref": "32676979",
        "price": 9.49,
        "proof_currency": "USD",
        "located_in_wikidata": "Q28227933"
    }
    """

    name = "mortonwilliams_us"
    allowed_domains = ["shop.mortonwilliams.com"]
    sitemap_urls = [
        "https://shop.mortonwilliams.com/sitemaps/storefront_pro/shop_mortonwilliams_com/sitemap.xml"
    ]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "proof_currency": "USD",
        "located_in_wikidata": "Q28227933",
    }

    def post_process_item(self, item, response, ld_data):
        if item.get("offers"):
            price = item["offers"][0].get("price")
            if price:
                item["price"] = float(price)

        if brand := ld_data.get("brand"):
            if isinstance(brand, dict):
                item["brand"] = brand.get("name")
            else:
                item["brand"] = brand

        yield item
