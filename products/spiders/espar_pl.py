from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class EsparPLSpider(SitemapSpider, StructuredDataSpider):
    name = "espar_pl"
    allowed_domains = ["e-spar.com.pl"]
    item_attributes = {
        "extras": {"seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q610492", "name": "SPAR"}}
    }
    sitemap_urls = ["https://e-spar.com.pl/robots.txt"]
    sitemap_rules = [
        (r"https://e-spar.com.pl/towar/[\w-]+/[\d]+", "parse_sd"),
    ]
