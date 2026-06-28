from products.edgesweet import EdgesweetSpider


class RalphsUSSpider(EdgesweetSpider):
    """
    Ralphs (United States) spider.
    Wikidata: Q3929820
    Sample URL: https://www.ralphs.com/p/green-asparagus/0000000004080
    """

    name = "ralphs_us"
    allowed_domains = ["ralphs.com"]
    sitemap_urls = ["https://www.ralphs.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3929820",
                "name": "Ralphs",
            }
        }
    }
