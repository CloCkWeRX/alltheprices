from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class YaokoNetSpider(SitemapSpider, StructuredDataSpider):
    name = "yaoko_net"
    allowed_domains = ["yaoko-net.com"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q11344967", "name": "Yaoko"}
        }
    }

    sitemap_urls = ["https://www.yaoko-net.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.yaoko-net.com/product/detail/[\w-]+.html", "parse_sd"),
    ]
