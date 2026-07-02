import json
import base64
import re
from scrapy import Request, Spider
from products.items import Product

class KlasikoBGSpider(Spider):
    name = "klasiko_bg"
    allowed_domains = ["klasiko.bg"]
    start_urls = ["https://klasiko.bg/"]

    def parse(self, response):
        # Extract category links which have the filter parameter
        category_links = response.css('a[href*="filter="]::attr(href)').getall()
        filters = set()
        for link in category_links:
            match = re.search(r"filter=([^&]+)", link)
            if match:
                filters.add(match.group(1))

        for f in filters:
            yield self.make_ajax_request(f, page=1)

    def make_ajax_request(self, filter_val, page):
        url = f"https://klasiko.bg/index.php?ajax_module=catalog&mod=ajax&action=showResults&current_page={page}&per_page=100&filter={filter_val}"
        return Request(
            url,
            callback=self.parse_ajax,
            meta={"filter_val": filter_val, "page": page},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def parse_ajax(self, response):
        data = json.loads(response.text)
        html_content = data.get("data", "")
        if not html_content:
            return

        # Use a temporary response to parse the HTML snippet
        selector = response.replace(body=html_content.encode("utf-8"))

        product_links = selector.css(".p-image a::attr(href)").getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)

        # Pagination: the site seems to load more on scroll.
        # We can try to increment page until we get no more data.
        # The JS says: if( response.data ) { ... showPage++; }
        if len(product_links) > 0:
            next_page = response.meta["page"] + 1
            yield self.make_ajax_request(response.meta["filter_val"], next_page)

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("h1::text").get() or \
               response.css(".details-title::text").get() or \
               response.css(".p-name::text").get()
        if not name:
             # Fallback to title if h1 is not found or empty
             name = response.xpath("//title/text()").get()
             if name:
                 name = name.split("-")[0].strip()

        product["name"] = name.strip() if name else None

        # Price extraction
        # <span class="price">4<sup>.69</sup> <span class="currency">лв/кг</span></span>
        # We prefer BGN (лв)
        price_selectors = response.css(".p-prices .price")
        bgn_price_selector = None
        for ps in price_selectors:
            currency = ps.css(".currency::text").get()
            if currency and "лв" in currency:
                bgn_price_selector = ps
                product["price_per"] = currency.strip().replace("лв/", "")
                break

        if bgn_price_selector:
            main_price = bgn_price_selector.xpath("text()").get()
            sup_price = bgn_price_selector.css("sup::text").get()
            if main_price and sup_price:
                price_str = main_price.strip() + sup_price.strip()
                try:
                    product["price"] = float(price_str)
                except ValueError:
                    pass
            elif main_price:
                try:
                    product["price"] = float(main_price.strip())
                except ValueError:
                    pass

        product["image"] = response.css(".p-image img::attr(src)").get()

        # Table details
        rows = response.css("table tr")
        for row in rows:
            label = row.css("td:first-child::text").get()
            value = row.css("td:last-child strong::text").get()
            if label and value:
                if "Марка" in label:
                    product["brand"] = value.strip()
                elif "Продуктов код" in label:
                    product["ref"] = value.strip()

        yield product
