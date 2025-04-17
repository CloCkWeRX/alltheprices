from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class AswakassalamMASpider(SitemapSpider, StructuredDataSpider):
    name = "aswakassalam_ma"
    allowed_domains = ["aswakassalam.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2868678",
                "name": "Aswak Assalam",
            }
        }
    }

    sitemap_urls = ["https://aswakassalam.com/robots.txt"]
    sitemap_rules = [
        (r"https://aswakassalam.com/produit/[\w-]+", "parse_sd"),
    ]
