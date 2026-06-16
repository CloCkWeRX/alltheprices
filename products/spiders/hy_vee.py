from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class HyVeeSpider(SitemapSpider, StructuredDataSpider):
    name = "hy_vee"
    allowed_domains = ["hy-vee.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1639719",
                "name": "Hy-Vee",
            }
        }
    }

    sitemap_urls = ["https://www.hy-vee.com/sitemap-aisles-online-products-index.xml"]
    sitemap_rules = [
        (r"/aisles-online/p/(\d+)", "parse_sd"),
    ]
