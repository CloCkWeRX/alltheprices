from products.edgesweet import EdgesweetSpider


class SmithsfoodanddrugUSSpider(EdgesweetSpider):
    """
    Smith's Food and Drug (United States) spider.
    Wikidata: Q7544856
    Sample URL: https://www.smithsfoodanddrug.com/p/fresh-blackberries/0003338324000
    """

    name = "smithsfoodanddrug_us"
    allowed_domains = ["smithsfoodanddrug.com"]
    sitemap_urls = ["https://www.smithsfoodanddrug.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7544856",
                "name": "Smith's Food and Drug",
            }
        }
    }
