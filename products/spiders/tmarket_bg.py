from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class TmarketBGSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for T Market (Bulgaria).
    Uses SitemapSpider with StructuredDataSpider to parse product JSON-LD data.
    Wikidata: Q64033983 (T Market)

    Sample output:
    {
        "name": "Кашкавал МАДЖАРОВ без лактоза 380г",
        "website": "https://tmarketonline.bg/product/kashkaval-madjarov-bez-laktoza-380g",
        "image": "https://tmarketonline.bg/cdn/img/products/56421/kaskaval-madzarov-bez-laktoza-380g-6a3246fd3821f.jpeg?width=1920&height=1920&v=1781679869",
        "ref": "1395036",
        "sku": "1395036",
        "brand": "ДИМИТЪР МАДЖАРОВ",
        "located_in_wikidata": "Q64033983"
    }
    """

    name = "tmarket_bg"
    allowed_domains = ["tmarketonline.bg"]
    sitemap_urls = ["https://tmarketonline.bg/sitemap.xml"]
    sitemap_rules = [(r"/product/([^/]+)$", "parse_sd")]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q64033983",
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if "loc" in entry and "/product/" in entry["loc"]:
                yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["located_in_wikidata"] = "Q64033983"

        # Force proof currency to EUR if price is in EUR
        if item.get("price") and not item.get("proof_currency"):
            # StructuredDataSpider promotes the price and tries to set proof_currency from Offers
            pass

        yield item
