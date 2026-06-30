from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST
from scrapy.spiders import SitemapSpider


class SproutsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sprouts_us"
    allowed_domains = ["shop.sprouts.com"]
    sitemap_urls = [
        "https://shop.sprouts.com/sitemaps/storefront_pro/shop_sprouts_com/sitemap.xml"
    ]
    sitemap_rules = [(r"/products/(\d+)-", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7581369",
                "name": "Sprouts Farmers Market",
            }
        }
    }
