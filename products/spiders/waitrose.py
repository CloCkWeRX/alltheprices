from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class WaitroseSpider(SitemapSpider, StructuredDataSpider):
    name = "waitrose"
    allowed_domains = ["waitrose.com"]

    sitemap_urls = ["https://www.waitrose.com/sitemapIndex.xml"]
    sitemap_rules = [
        (r"https://www.waitrose.com/ecom/products/[\w-]+/[\d-]+", "parse_sd"),
    ]
