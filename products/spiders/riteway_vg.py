from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class RitewayVGSpider(SitemapSpider, StructuredDataSpider):
    name = "riteway_vg"
    allowed_domains = ["riteway.vg"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q133882237",
                "name": "RiteWay Food Markets",
            }
        }
    }

    sitemap_urls = ["https://www.riteway.vg/robots.txt"]
    sitemap_rules = [
        (r"https://www.riteway.vg/[\w-]+", "parse_sd"),
    ]
