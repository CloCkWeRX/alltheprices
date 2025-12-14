from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class MorrisonsSpider(SitemapSpider, StructuredDataSpider):
    name = "morrisons"
    allowed_domains = ["groceries.morrisons.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q922344",
                "name": "Morrisons",
            }
        }
    }

    sitemap_urls = ["https://groceries.morrisons.com/robots.txt"]
    sitemap_rules = [
        (r"https://groceries.morrisons.com/products/[\w-]+/\d+", "parse_sd"),
    ]
