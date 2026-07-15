import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class BoothsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "booths_gb"
    allowed_domains = ["booths.co.uk"]
    sitemap_urls = [
        "https://www.booths.co.uk/sitemap_index.xml",
    ]
    sitemap_follow = [
        r"beer-sitemap\.xml",
        r"offer-sitemap\.xml",
    ]
    sitemap_rules = [
        (r"/beer/([^/]+)/$", "parse_sd"),
        (r"/offer/(\d+)/$", "parse_sd"),
    ]

    # Required metadata
    dataset_attributes = {
        "source": "structured_data",
        "wikidata": "Q4943949",
    }

    # Custom settings to handle realistic User-Agent and Robots.txt policy
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    }

    def parse_sd(self, response):
        # First, try standard structured data extraction
        items = list(super().parse_sd(response))
        if items:
            yield from items
            return

        # If no standard Product structured data was found, fallback to bespoke HTML extraction.
        item = Product(
            name=None,
            price=None,
            proof_currency=None,
            brand="Booths",
            description=None,
            image=None,
            ref=None,
            website=response.url,
        )
        yield from self.post_process_item(item, response, {})

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # Extract name if not already extracted
        if not item.get("name"):
            name = response.xpath("//h2/text()").get()
            if not name:
                name = response.xpath("//div[@id='wineTitle']/h2/text()").get()
            if not name:
                name = response.xpath("//title/text()").get()
                if name:
                    name = name.replace(" - Booths", "").strip()
            if name:
                item["name"] = name.strip()

        # Extract price if not already extracted
        if not item.get("price"):
            price_text = response.xpath("//div[@id='priceLabel']/text()").get()
            if price_text:
                price_clean = re.sub(r"[^\d\.]", "", price_text)
                if price_clean:
                    item["price"] = price_clean
                    item["proof_currency"] = "GBP"

        # Extract image if not already extracted
        if not item.get("image"):
            image_src = response.xpath("//div[@id='secondHalfOfWinePage']//img/@src").get()
            if not image_src:
                image_src = response.xpath("//img[contains(@src, 'wp-content/beer')]/@src").get()
            if not image_src:
                image_src = response.xpath("//img[contains(@src, '/wp-content/')]/@src").get()

            if image_src and "placehold.it" not in image_src:
                item["image"] = response.urljoin(image_src)

        # Extract description/tasting notes
        if not item.get("description"):
            tasting_notes = response.xpath("//div[@id='wineDetails']/p/text()").getall()
            if tasting_notes:
                item["description"] = " ".join([t.strip() for t in tasting_notes if t.strip()])

        # Extract ref/unique identifier
        if not item.get("ref"):
            image_src = item.get("image") or ""
            barcode_match = re.search(r"/(\d{8,14})\.(jpg|png|jpeg)", image_src)
            if barcode_match:
                item["ref"] = barcode_match.group(1)
                item["gtin"] = barcode_match.group(1)

        # Fallback for ref if still not set
        if not item.get("ref"):
            # Extract from the URL slug
            slug_match = re.search(r"/(beer|offer)/([^/]+)/$", response.url)
            if slug_match:
                item["ref"] = slug_match.group(2)

        yield item
