from products.edgesweet import EdgesweetSpider


class DillonsUSSpider(EdgesweetSpider):
    """
    Dillons (United States) spider.
    Wikidata: Q5276954
    Sample URL: https://www.dillons.com/p/king-s-hawaiian-original-sweet-dinner-rolls/0007343500004
    """

    name = "dillons_us"
    allowed_domains = ["dillons.com"]
    sitemap_urls = ["https://www.dillons.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5276954",
                "name": "Dillons",
            }
        }
    }
