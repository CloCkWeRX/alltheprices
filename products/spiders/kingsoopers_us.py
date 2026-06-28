from products.edgesweet import EdgesweetSpider


class KingsoopersUSSpider(EdgesweetSpider):
    """
    King Soopers (United States) spider.
    Wikidata: Q6412065
    Sample URL: https://www.kingsoopers.com/p/green-asparagus/0000000004080
    """

    name = "kingsoopers_us"
    allowed_domains = ["kingsoopers.com"]
    sitemap_urls = ["https://www.kingsoopers.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6412065",
                "name": "King Soopers",
            }
        }
    }
