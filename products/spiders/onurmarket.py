from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class OnurmarketSpider(SitemapSpider, StructuredDataSpider):
    name = "onurmarket"
    allowed_domains = ["onurmarket.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q127273067",
                "name": "Onur Market",
            }
        }
    }

    sitemap_urls = ["https://www.onurmarket.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.onurmarket.com/[\w-]+", "parse_sd"),
    ]
