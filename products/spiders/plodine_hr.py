import re
import hashlib
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class PlodineHRSpider(Spider):
    """
    Spider for Plodine (Croatia).
    Retailer website: https://www.plodine.hr/
    Wikidata: Q58040098 (Plodine d.d.)

    Since Plodine does not have a sitemap and lacks individual product detail pages (PDPs) in search engines,
    we crawl:
    1. Private label brand pages ("robne marke"): e.g., https://www.plodine.hr/robne-marke
       This displays all Plodine's private label brands (e.g., Alegro, Doline, Boni, Esens).
       We extract the listed products, grouping them by their specific brand.
    2. Promotion/campaign pages: e.g., tjedna ponuda (weekly offers), vikend ponuda (weekend offers),
       and početak tjedna (beginning of the week offers) where prices are explicitly listed.

    Sample output item:
    {
        "name": "Badem jezgra",
        "website": "https://www.plodine.hr/robna-marka/60/alegro",
        "image": "https://www.plodine.hr/uploads/web-plodine-alegro-badem-180g-976426.jpg",
        "ref": "976426",
        "description": "180 g",
        "brand": "Alegro",
        "located_in_wikidata": "Q58040098"
    }
    """

    name = "plodine_hr"
    allowed_domains = ["plodine.hr"]
    start_urls = [
        "https://www.plodine.hr/robne-marke",
        "https://www.plodine.hr/akcije/79/tjedna-ponuda/izdvojeno",
        "https://www.plodine.hr/akcije/10/vikend-ponuda",
        "https://www.plodine.hr/akcije/11/pocetak-tjedna",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "CONCURRENT_REQUESTS": 16,
        "DOWNLOAD_DELAY": 0.2,
    }

    def parse(self, response):
        # Determine page type based on URL
        if "robne-marke" in response.url:
            # We are on the main brands page
            brand_links = response.css('a[href*="/robna-marka/"]::attr(href)').getall()
            for link in brand_links:
                yield response.follow(link, self.parse_brand)
        elif "akcije" in response.url:
            # We are on a promotion page
            yield from self.parse_promo_page(response)

    def parse_brand(self, response):
        # Extract brand name
        brand_name = response.css('h1::text').get()
        if not brand_name:
            brand_name = response.url.split('/')[-1].replace('-', ' ').title()
        brand_name = brand_name.strip()

        # Extract products
        products = response.css('article.card--01')
        for prod in products:
            item = Product()
            name = prod.css('.card__title::text').get()
            if not name:
                continue
            name = name.strip()

            quantity = prod.css('.card__quantity::text').get()
            if quantity:
                item["description"] = quantity.strip()

            img_src = prod.css('img.card__img::attr(src)').get()
            if img_src:
                item["image"] = response.urljoin(img_src)
                # Extract ref/ID from image source if possible, else fallback to hashing name
                # E.g., web-plodine-alegro-badem-180g-976426.jpg -> 976426
                match = re.search(r'-(\d+)(?:\([^)]+\))?\.jpe?g', img_src, re.IGNORECASE)
                if match:
                    item["ref"] = match.group(1)
                else:
                    # Clean the filename for numbers
                    filename = img_src.split('/')[-1]
                    digits = re.findall(r'\d+', filename)
                    if digits and len(digits[-1]) >= 4:
                        item["ref"] = digits[-1]
                    else:
                        item["ref"] = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
            else:
                item["ref"] = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]

            item["name"] = name
            item["brand"] = brand_name
            item["website"] = response.url
            item["located_in_wikidata"] = "Q58040098"

            yield item

    def parse_promo_page(self, response):
        products = response.css('article.card--01')
        for prod in products:
            item = Product()
            name = prod.css('.card__title::text').get()
            if not name:
                continue
            name = name.strip()

            brand_desc = prod.css('.card__description::text').get()
            if brand_desc:
                item["brand"] = brand_desc.strip()

            quantity = prod.css('.card__quantity::text').get()
            if quantity:
                item["description"] = quantity.strip()

            img_src = prod.css('img.card__img::attr(src)').get()
            if img_src:
                item["image"] = response.urljoin(img_src)
                match = re.search(r'-(\d+)(?:\([^)]+\))?\.jpe?g', img_src, re.IGNORECASE)
                if match:
                    item["ref"] = match.group(1)
                else:
                    filename = img_src.split('/')[-1]
                    digits = re.findall(r'\d+', filename)
                    if digits and len(digits[-1]) >= 4:
                        item["ref"] = digits[-1]
                    else:
                        item["ref"] = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
            else:
                item["ref"] = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]

            item["name"] = name
            item["website"] = response.url
            item["located_in_wikidata"] = "Q58040098"

            # Parse offers / price
            # e.g., <p class="regular"><strong>5,59</strong> € </p>
            price_strong = prod.css('.card__price strong::text').get()
            if price_strong:
                price_str = price_strong.strip().replace('.', '').replace(',', '.')
                try:
                    price_val = float(price_str)
                    item["offers"] = [{
                        "@type": "Offer",
                        "price": price_val,
                        "priceCurrency": "EUR",
                        "availability": "https://schema.org/InStock",
                    }]
                except ValueError:
                    pass

            yield item
