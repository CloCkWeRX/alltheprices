from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BoothsGBSpider(SitemapSpider, StructuredDataSpider):
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
        (r"https://orders.booths.co.uk/[\w-]+.html", "parse_sd"),
    ]
