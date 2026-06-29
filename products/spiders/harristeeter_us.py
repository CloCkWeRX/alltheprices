from products.edgesweet import EdgesweetSpider


class HarristeeterUSSpider(EdgesweetSpider):
    """
    Harris Teeter (United States) spider.
    Wikidata: Q5665067
    Sample URL: https://www.harristeeter.com/p/fresh-blackberries/0003338324000
    """

    name = "harristeeter_us"
    allowed_domains = ["harristeeter.com"]
    sitemap_urls = ["https://www.harristeeter.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5665067",
                "name": "Harris Teeter",
            }
        }
    }
