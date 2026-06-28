from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class RosauersUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Rosauers (US) spider.
    Wikidata: Q7367458

    Sample output structured data:
    {
        "name": "Rosauers From-Scratch Bakery Muffins",
        "website": "https://shop.rosauers.com/store/rosauers-supermarkets/products/26558163-b2g1-raspberry-muffins-64-oz",
        "image": "https://d1s8987jlndkbs.cloudfront.net/assets/missing-item-4bbe82b8555e4d1c12626fd482cb2409713e8e30835645ff3650ef66a725d03c.png",
        "ref": "26558163",
        "sku": "26558163",
        "offers": [
            {
                "@type": "Offer",
                "price": "6.99",
                "priceCurrency": "USD",
                "url": "https://shop.rosauers.com/store/rosauers-supermarkets/products/26558163-b2g1-raspberry-muffins-64-oz",
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7367458",
                "name": "Rosauers"
            }
        }
    }
    """

    name = "rosauers_us"
    allowed_domains = ["rosauers.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7367458",
                "name": "Rosauers",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
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
