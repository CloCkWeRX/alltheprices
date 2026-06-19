from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BulmagOrgSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for BulMag (Bulgaria).
    Exposes schema.org/Product in JSON-LD.

    Sample item:
    {
        "name": "Капсули ариел japan blossom 60бр",
        "image": "https://api.bulmag.org/images/fe57b63f7bd4705cab4f9cf52d96eed8.png",
        "ref": "7700",
        "website": "https://bulmag.org/product/kapsuli-ariel-japan-blossom-60br",
        "offers": [
            {
                "@type": "Offer",
                "price": 26.29,
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "name": "BulMag"
            }
        }
    }
    """

    name = "bulmag_org"
    allowed_domains = ["bulmag.org"]
    item_attributes = {"extras": {"seller": {"@type": "Organization", "name": "BulMag"}}}

    sitemap_urls = ["https://bulmag.org/robots.txt"]
    sitemap_rules = [
        (r"/product/([\w-]+)", "parse_sd"),
    ]
