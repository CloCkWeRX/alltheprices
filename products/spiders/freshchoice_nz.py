from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

# https://cannonscreek.store.freshchoice.co.nz/ is the primary store
class FreshchoiceNZSpider(SitemapSpider, StructuredDataSpider):
    name = "freshchoice_nz"
    allowed_domains = ["cannonscreek.store.freshchoice.co.nz"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q22271877",
                "name": "FreshChoice",
            }
        }
    }

    sitemap_urls = ["https://cannonscreek.store.freshchoice.co.nz/sitemap.xml"]
    sitemap_rules = [
        (r"https://cannonscreek.store.freshchoice.co.nz/lines/[\w-]+", "parse_sd"),
    ]
