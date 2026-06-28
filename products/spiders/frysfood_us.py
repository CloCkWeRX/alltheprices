from products.edgesweet import EdgesweetSpider


class FrysfoodUSSpider(EdgesweetSpider):
    """
    Fry's Food and Drug (United States) spider.
    Wikidata: Q5506547
    Sample URL: https://www.frysfood.com/p/kroger-grade-a-large-white-eggs/0001111060933
    """

    name = "frysfood_us"
    allowed_domains = ["frysfood.com"]
    sitemap_urls = ["https://www.frysfood.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5506547",
                "name": "Fry's Food and Drug",
            }
        }
    }
