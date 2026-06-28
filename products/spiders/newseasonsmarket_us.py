from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class NewseasonsmarketUSSpider(SitemapSpider, StructuredDataSpider):
    """
    New Seasons Market (United States) spider.
    Wikidata: Q7011463
    """

    name = "newseasonsmarket_us"
    allowed_domains = ["newseasonsmarket.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7011463",
                "name": "New Seasons Market",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://shop.newseasonsmarket.com/sitemaps/storefront_pro/shop_newseasonsmarket_com/products/sitemap0.xml",
        "https://shop.newseasonsmarket.com/sitemaps/storefront_pro/shop_newseasonsmarket_com/products/sitemap1.xml",
    ]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]
