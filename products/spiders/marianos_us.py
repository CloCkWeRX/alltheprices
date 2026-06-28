from products.edgesweet import EdgesweetSpider


class MarianosUSSpider(EdgesweetSpider):
    """
    Mariano's (United States) spider.
    Wikidata: Q55622168
    Sample URL: https://www.marianos.com/p/brussels-sprouts/0003338370154
    """

    name = "marianos_us"
    allowed_domains = ["marianos.com"]
    sitemap_urls = ["https://www.marianos.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q55622168",
                "name": "Mariano's",
            }
        }
    }
