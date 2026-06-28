from products.edgesweet import EdgesweetSpider


class CitymarketUSSpider(EdgesweetSpider):
    """
    City Market (United States) spider.
    Wikidata: Q5123299
    Sample URL: https://www.citymarket.com/p/kroger-russet-potatoes/0001111091760
    """

    name = "citymarket_us"
    allowed_domains = ["citymarket.com"]
    sitemap_urls = ["https://www.citymarket.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5123299",
                "name": "City Market",
            }
        }
    }
