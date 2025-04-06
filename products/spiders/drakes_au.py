import scrapy

from scrapy.spiders import SitemapSpider
from scrapy.http import Request, Response, XmlResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider


class DrakesAUSpider(CrawlSpider, SitemapSpider, StructuredDataSpider):
    name = "drakes_au"

    sitemap_rules = [
        (r"/lines/[\w-]+", "parse_sd"),
    ]
    allowed_domains = ["drakes.com.au"]
    start_urls = ["https://online.drakes.com.au/multipage"]

    rules = (
        Rule(LinkExtractor(allow=(r"i_choose_you",)), callback="detect_subdomain"),
    )

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self._parse)

    def detect_subdomain(self, response):
        yield Request(response.url + "sitemap.xml", self._parse_sitemap)
