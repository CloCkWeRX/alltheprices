from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class HalpahalliFISpider(SitemapSpider, StructuredDataSpider):
    name = "halpahalli_fi"
    allowed_domains = ["halpahalli.fi"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11861256",
                "name": "Kokkolan Halpa-Halli Oy",
            }
        }
    }

    sitemap_urls = ["https://www.halpahalli.fi/media/sitemap/sitemap_product.xml"]
    sitemap_rules = [
        # https://www.halpahalli.fi/del-monte-persikanpuolikkaat-mehussa-415g.html
        (r"https://www.halpahalli.fi/[\w-]+\.html", "parse_sd"),
    ]
