from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class PricechopperUSSpider(SitemapSpider, StructuredDataSpider):
    """
    Price Chopper (Northeastern United States) spider.
    Wikidata: Q7242574

    Sample output structured data:
    {
        "name": "Entenmann's 6 ct, Powdered, Donuts, Donuts, 3 oz",
        "website": "https://shop.pricechopper.com/store/price-chopper-ny/products/29529442-entenmann-s-powdered-donuts-3-oz",
        "description": "Moist golden cake coated with sweet powdered sugar, Entenmanns Powdered Mini Donuts put the POW in powdered donuts",
        "image": "https://d2lnr5mha7bycj.cloudfront.net/product-image/file/large_68024d44-6270-4f3d-a101-d436131ea2da.png",
        "ref": "29529442",
        "sku": "29529442",
        "brand": "Entenmann's",
        "offers": [
            {
                "@type": "Offer",
                "price": "1.99",
                "priceCurrency": "USD",
                "url": "https://shop.pricechopper.com/store/price-chopper-ny/products/29529442-entenmann-s-powdered-donuts-3-oz",
                "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7242574",
                "name": "Price Chopper"
            }
        }
    }
    """

    name = "pricechopper_us"
    allowed_domains = ["pricechopper.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7242574",
                "name": "Price Chopper",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://shop.pricechopper.com/sitemaps/storefront_pro/shop_pricechopper_com/products/sitemap0.xml",
        "https://shop.pricechopper.com/sitemaps/storefront_pro/shop_pricechopper_com/products/sitemap1.xml",
        "https://shop.pricechopper.com/sitemaps/storefront_pro/shop_pricechopper_com/products/sitemap2.xml",
    ]
    sitemap_rules = [
        (r"/products/(\d+)-", "parse_sd"),
    ]
