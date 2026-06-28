from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class GelsonsUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Gelson's Markets (United States) spider.
    Wikidata: Q16993993
    """

    name = "gelsons_us"
    allowed_domains = ["gelsons.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q16993993",
                "name": "Gelson's Markets",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://shop.gelsons.com/sitemaps/storefront_pro/shop_gelsons_com/products/sitemap0.xml",
    ]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]
