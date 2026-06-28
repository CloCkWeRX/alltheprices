from products.edgesweet import EdgesweetSpider


class QfcUSSpider(EdgesweetSpider):
    """
    QFC (United States) spider.
    Wikidata: Q7265425
    Sample URL: https://www.qfc.com/p/fresh-blackberries/0003338324000
    """

    name = "qfc_us"
    allowed_domains = ["qfc.com"]
    sitemap_urls = ["https://www.qfc.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7265425",
                "name": "QFC",
            }
        }
    }
