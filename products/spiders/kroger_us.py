from products.edgesweet import EdgesweetSpider


class KrogerUSSpider(EdgesweetSpider):
    """
    Kroger (United States) spider.
    Wikidata: Q153417
    Sample URL: https://www.kroger.com/p/red-seedless-grapes/0000000004023
    """

    name = "kroger_us"
    allowed_domains = ["kroger.com"]
    sitemap_urls = ["https://www.kroger.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q153417",
                "name": "Kroger",
            }
        }
    }
