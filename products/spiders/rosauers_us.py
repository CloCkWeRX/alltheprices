from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class RosauersUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Rosauers Supermarkets (United States) spider.
    Wikidata: Q7367458
    """

    name = "rosauers_us"
    allowed_domains = ["rosauers.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7367458",
                "name": "Rosauers Supermarkets",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://shop.rosauers.com/sitemaps/storefront_pro/shop_rosauers_com/products/sitemap0.xml",
        "https://shop.rosauers.com/sitemaps/storefront_pro/shop_rosauers_com/products/sitemap1.xml",
        "https://shop.rosauers.com/sitemaps/storefront_pro/shop_rosauers_com/products/sitemap2.xml",
    ]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]
