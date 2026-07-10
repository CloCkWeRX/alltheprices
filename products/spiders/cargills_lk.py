import re
import json
from urllib.parse import urlparse, parse_qs
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class CargillsLkSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Cargills Online (Sri Lanka).
    Uses Playwright to handle AngularJS hydration for prices.
    Wikidata: Q5039260 (Cargills Ceylon PLC)

    Sample output:
    {
        "name": "Maliban UHT Fresh Milk",
        "image": "https://cargillsonline.com/VendorItems/MenuItems/BVE0423_1.png",
        "website": "https://cargillsonline.com/ProductDetails/Dairy/Maliban-UHT-Fresh-Milk?ID=%20m3HoM0QUMweV4aM2j%20LEw==",
        "ref": " m3HoM0QUMweV4aM2j LEw==",
        "price": "550.00",
        "proof_currency": "LKR",
        "located_in_wikidata": "Q5039260"
    }
    """
    name = "cargills_lk"
    allowed_domains = ["cargillsonline.com"]
    start_urls = ["https://cargillsonline.com/"]

    rules = (
        Rule(
            LinkExtractor(allow=r"/Product/[^?]+"),
            follow=True,
            process_request="add_playwright"
        ),
        Rule(
            LinkExtractor(allow=r"/ProductDetails/"),
            callback="parse_product",
            process_request="add_playwright_product"
        ),
    )

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_urls := kwargs.get("start_urls"):
            if isinstance(start_urls, str) and start_urls.startswith("["):
                self.start_urls = json.loads(start_urls)
            elif isinstance(start_urls, str):
                self.start_urls = [start_urls]

    def start_requests(self):
        for url in self.start_urls:
            if "/ProductDetails/" in url:
                yield self.add_playwright_product(scrapy.Request(url, callback=self.parse_product))
            else:
                yield self.add_playwright(scrapy.Request(url))

    def add_playwright(self, request, response=None):
        request.meta["playwright"] = True
        return request

    def add_playwright_product(self, request, response=None):
        request.meta["playwright"] = True
        request.meta["playwright_page_methods"] = [
            PageMethod("wait_for_selector", "h4:has-text('Rs.')", timeout=30000),
        ]
        return request

    def parse_product(self, response):
        item = Product()

        name = response.xpath('//meta[@property="og:title"]/@content').get()
        if not name:
            name = response.xpath("//h3[contains(@class, 'ned')]/text()").get()
        if name:
            item["name"] = name.strip()

        image = response.xpath('//meta[@property="og:image"]/@content').get()
        if image:
            item["image"] = response.urljoin(image.strip())

        item["website"] = response.url

        query = parse_qs(urlparse(response.url).query)
        if "ID" in query:
            item["ref"] = query["ID"][0]
        else:
            item["ref"] = response.url

        price_text = response.xpath("//h4[contains(., 'Rs.')]//text()").getall()
        price_text = " ".join(price_text)
        match = re.search(r"Rs\.?\s*([\d,.]+)", price_text)
        if match:
            item["price"] = match.group(1).replace(",", "")
            item["proof_currency"] = "LKR"
        else:
            all_text = response.xpath("//body//text()").getall()
            all_text = " ".join(all_text)
            match = re.search(r"Rs\.?\s*([\d,.]+)", all_text)
            if match:
                item["price"] = match.group(1).replace(",", "")
                item["proof_currency"] = "LKR"

        item["located_in_wikidata"] = "Q5039260"

        yield item
