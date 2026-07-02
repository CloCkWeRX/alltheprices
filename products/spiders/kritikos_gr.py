import re
import json
from datetime import datetime
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from scrapy_playwright.page import PageMethod
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class KritikosGRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Kritikos Supermarkets (Greece).
    Wikidata: Q129911567
    The site uses Next.js and prices are loaded dynamically.
    """

    name = "kritikos_gr"
    allowed_domains = ["kritikos-sm.gr"]
    sitemap_urls = [
        "https://kritikos-sm.gr/sitemap-1.xml",
        "https://kritikos-sm.gr/sitemap-2.xml",
    ]
    sitemap_rules = [(r"/products/.*-\d+/", "parse_product")]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type in ["image", "font", "media"],
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q129911567",
                "name": "Kritikos",
            }
        }
    }

    def start_requests(self):
        yield Request(
            "https://kritikos-sm.gr/",
            callback=self.parse_home,
            meta={
                "playwright": True,
                "playwright_include_page": False,
            },
        )

    def parse_home(self, response):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_include_page"] = False
                    request_or_item.meta["playwright_page_methods"] = [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_timeout", 5000),
                    ]
                yield request_or_item
            else:
                yield request_or_item

    def parse_product(self, response: Response):
        # Extract from NEXT_DATA if available for metadata
        next_data_script = response.css('script#__NEXT_DATA__::text').get()
        product_data = {}
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                page_props = data.get('props', {}).get('pageProps', {})
                product_details = page_props.get('productDetails', {})
                if product_details:
                    product_data['name'] = page_props.get('productDetailsTitle')
                    product_data['sku'] = product_details.get('sku')
                    product_data['description'] = product_details.get('description')
                    product_data['image'] = page_props.get('imgSrc')
            except Exception:
                pass

        # If NEXT_DATA parsing failed or is incomplete, use CSS
        if not product_data.get('name'):
            product_data['name'] = response.css('h1::text').get()
        if not product_data.get('sku'):
            sku_text = response.xpath('//*[contains(text(), "Κωδ. προϊόντος")]/text()').get()
            if sku_text:
                sku_match = re.search(r'(\d+)', sku_text)
                if sku_match:
                    product_data['sku'] = sku_match.group(1)

        # Price is dynamic, extracted from rendered DOM
        # Selector examples: span.ProductDetails_price__9wMeq
        price_text = response.css('span[class*="ProductDetails_price__"]::text').get()
        if not price_text:
            price_text = response.css('p[class*="ProductDetails_priceText__"] span::text').get()
        if not price_text:
            # Fallback to any element that looks like a price if the specific class is not there
            # Filter for elements that actually have a price format to avoid noise
            price_text = response.xpath('//span[contains(text(), "€") and re:test(text(), "\d+")]/text()').get()

        price = None
        if price_text:
            # Clean "€ 2.62 " -> 2.62
            price_cleaned = price_text.replace('€', '').replace(',', '.').strip()
            price_match = re.search(r'(\d+(?:\.\d+)?)', price_cleaned)
            if price_match:
                price = float(price_match.group(1))

        item = self.get_default_item(response)
        item['name'] = (product_data.get('name') or '').strip()
        item['sku'] = product_data.get('sku')
        item['ref'] = product_data.get('sku')
        item['description'] = product_data.get('description')
        item['image'] = (
            product_data.get('image') or
            response.xpath('//meta[@property="og:image"]/@content').get() or
            response.css('img[src*="/products/"]::attr(src)').get()
        )

        if price is not None:
            item['price'] = price
            item['proof_currency'] = "EUR"
            item['offers'] = [{
                "@type": "Offer",
                "price": price,
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock",
                "url": response.url
            }]

        yield item

    def get_default_item(self, response: Response) -> Product:
        return Product(
            website=response.url,
            date=datetime.now().isoformat(),
        )

    def get_ref(self, url: str, response: Response = None) -> str:
        match = re.search(r"/products/.*-(\d+)/$", url)
        if match:
            return match.group(1)
        return super().get_ref(url, response)
