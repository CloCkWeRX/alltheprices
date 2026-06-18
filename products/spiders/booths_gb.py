from scrapy.spiders import SitemapSpider

from products.open_graph_spider import OpenGraphSpider


class BoothsGBSpider(SitemapSpider, OpenGraphSpider):
    name = "booths_gb"
    allowed_domains = ["booths.co.uk"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4943949",
                "name": "Booths",
            }
        }
    }

    sitemap_urls = ["https://orders.booths.co.uk/robots.txt"]
    sitemap_rules = [
        (r"https://orders.booths.co.uk/[\w-]+.html", "parse_og"),
    ]
