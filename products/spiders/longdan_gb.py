from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class LongdanGBSpider(SitemapSpider, StructuredDataSpider):
    name = "longdan_gb"
    allowed_domains = ["longdan.co.uk"]

    sitemap_urls = ["https://longdan.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"https://longdan.co.uk/products/[\w-]+", "parse_sd"),
    ]
