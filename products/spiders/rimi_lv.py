from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class RimiLVSpider(SitemapSpider, StructuredDataSpider):
    name = "rimi_lv"
    allowed_domains = ["www.rimi.lv"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q104429659",
                "name": "Rimi Latvia",
            }
        }
    }

    sitemap_urls = ["https://www.rimi.lv/e-veikals/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.rimi.lv/e-veikals/en/products/(.*)/p/\d+", "parse_sd"),
    ]
