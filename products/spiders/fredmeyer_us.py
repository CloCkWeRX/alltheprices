from products.edgesweet import EdgesweetSpider


class FredmeyerUSSpider(EdgesweetSpider):
    """
    Fred Meyer (United States) spider.
    Wikidata: Q5495932
    Sample URL: https://www.fredmeyer.com/p/sugardale-ham-butt-portion-limit-1-at-sale-price/0024368950000
    """

    name = "fredmeyer_us"
    allowed_domains = ["fredmeyer.com"]
    sitemap_urls = ["https://www.fredmeyer.com/sitemap.xml"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5495932",
                "name": "Fred Meyer",
            }
        }
    }
