from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class VishalMegaMartSpider(SitemapSpider, StructuredDataSpider):
    name = "vishal_mega_mart"
    allowed_domains = ["vishalmegamart.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q126895037",
                "name": "Vishal Mega Mart",
            }
        }
    }

    sitemap_urls = ["https://www.vishalmegamart.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.vishalmegamart.com/en-in/food/[\w-]+.html", "parse_sd"),
    ]
