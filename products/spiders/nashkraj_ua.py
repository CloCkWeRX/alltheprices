import re

from scrapy.spiders import SitemapSpider

from products.items import Product


class NashkrajUASpider(SitemapSpider):
    """
    Nash Kraj (Ukraine) spider.
    """

    name = "nashkraj_ua"

    item_attributes = {
        "website": "nashkraj.ua",
        "brand_wikidata": "Q12132995",
        "proof_currency": "UAH",
    }

    allowed_domains = ["shop.nashkraj.ua"]
    sitemap_urls = [
        "https://shop.nashkraj.ua/sitemap.xml",
        "https://shop.nashkraj.ua/sitemap_11.xml",
        "https://shop.nashkraj.ua/sitemap_182.xml",
        "https://shop.nashkraj.ua/sitemap_2.xml",
        "https://shop.nashkraj.ua/sitemap_22.xml",
        "https://shop.nashkraj.ua/sitemap_29.xml",
        "https://shop.nashkraj.ua/sitemap_305.xml",
        "https://shop.nashkraj.ua/sitemap_332.xml",
        "https://shop.nashkraj.ua/sitemap_404.xml",
        "https://shop.nashkraj.ua/sitemap_419.xml",
        "https://shop.nashkraj.ua/sitemap_464.xml",
        "https://shop.nashkraj.ua/sitemap_82.xml",
        "https://shop.nashkraj.ua/sitemap_9.xml",
    ]
    sitemap_rules = [
        (r"/product/\d+-", "parse_product"),
    ]

    def parse_product(self, response):
        item = Product()

        # The product name is in an <h2> tag on the product page.
        # Fallback to <h1> or <title>.
        name = response.css("h2::text").get()
        if not name:
            name = response.css("h1::text").get()
        if not name:
            name = response.xpath("//title/text()").get()
        if name:
            item["name"] = name.strip()

        image = response.css("img.w-image-product::attr(src)").get()
        if image:
            item["image"] = response.urljoin(image)

        # Reference and GTIN - pick the first ones found
        ref = response.css("input[data-prod]::attr(data-prod)").get()
        if not ref:
            match = re.search(r"/product/(\d+)-", response.url)
            if match:
                ref = match.group(1)
        item["ref"] = ref

        gtin = response.css("strong[data-barcodes]::attr(data-barcodes)").get()
        if gtin:
            item["gtin"] = gtin
            if len(gtin) == 13:
                item["gtin13"] = gtin
            elif len(gtin) == 12:
                item["gtin12"] = gtin

        # Price extraction - limit to the first .price block which is the main product's price
        price_block = response.css(".price")[:1]

        price = price_block.css(".current_price::text").get()
        if not price:
            # Fallback to the first span in price block if current_price class is missing
            price = price_block.css("span::text").get()

        if price:
            price = price.strip().replace(" ", "").replace(",", ".")
            # Remove any non-numeric characters except the decimal point
            price = re.sub(r"[^\d.]", "", price)
            if price:
                item["price"] = price

        # Check for discount within the same price block
        old_price = price_block.css(".old_price::text").get()
        if old_price:
            old_price_val = old_price.strip().replace(" ", "").replace(",", ".")
            old_price_val = re.sub(r"[^\d.]", "", old_price_val)
            if old_price_val:
                item["price_is_discounted"] = True
                item["price_without_discount"] = old_price_val

        yield item
