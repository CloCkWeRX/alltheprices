import json
import re
from typing import Iterable
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class DekamarktNLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for DekaMarkt (Netherlands) (Q2489350).
    Fix #156.

    Sample output structured data:
    {
        "name": "Noord Hollandse Kaas - Jong belegen of belegen. Stuk 650 - 675 gram.",
        "website": "https://www.dekamarkt.nl/aanbiedingen",
        "image": "https://web-fileserver.dekamarkt.nl/offers/33-2026-Deka/f54eb356-9ec7-410c-88c7-4852a2aa8569.png?width=190",
        "ref": "136674",
        "sku": "136674",
        "located_in_wikidata": "Q2489350",
        "price": 4.99,
        "proof_currency": "EUR"
    }
    """

    name = "dekamarkt_nl"
    allowed_domains = ["dekamarkt.nl"]
    sitemap_urls = ["https://www.dekamarkt.nl/sitemap.xml"]
    sitemap_rules = [
        (r"/producten/", "parse_product"),
        (r"/aanbiedingen", "parse_offers"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
    }

    item_attributes = {
        "located_in_wikidata": "Q2489350",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2489350",
                "name": "DekaMarkt",
            }
        },
    }

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(url, callback=self.parse)
            return

        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def sitemap_filter(self, entries):
        for entry in entries:
            loc = entry["loc"]
            if ".xml" in loc:
                if "products-sitemap.xml" in loc or "categories-and-items-sitemap.xml" in loc:
                    yield entry
            else:
                yield entry

    def parse(self, response: Response, **kwargs):
        if "aanbiedingen" in response.url:
            yield from self.parse_offers(response)
        elif "/producten/" in response.url:
            yield from self.parse_product(response)
        else:
            yield from self.parse_sd(response)

    def parse_product(self, response: Response):
        """
        Extract product details from page HTML, Nuxt state, or fallback.
        """
        # First try standard structured data
        sd_items = list(self.parse_sd(response))
        if sd_items:
            yield from sd_items
            return

        # Fallback to parsing Nuxt state script
        nuxt_script = response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()
        if nuxt_script:
            try:
                nuxt_data = json.loads(nuxt_script)
                # Look for product ID or title strings in Nuxt array
                ref_match = re.search(r"/(\d+)$", response.url)
                ref = ref_match.group(1) if ref_match else None

                name = (
                    response.xpath('//meta[@property="og:title"]/@content').get()
                    or response.xpath("//h1/text()").get()
                    or response.xpath("//title/text()").get()
                )
                if name:
                    name = name.split("|")[0].strip()

                image = response.xpath('//meta[@property="og:image"]/@content').get()

                item = Product(
                    name=name,
                    website=response.url,
                    image=image,
                    ref=ref,
                    sku=ref,
                    proof_currency="EUR",
                    located_in_wikidata="Q2489350",
                )
                yield item
                return
            except Exception:
                pass

    def parse_offers(self, response: Response):
        """
        Extract products from offer listing cards.
        """
        cards = response.css("article.product__card")
        for card in cards:
            ref = card.attrib.get("data-product-id")
            if not ref:
                continue

            title = card.css("p.title::text").get()
            if not title:
                continue
            title = title.strip()

            addition = card.css("span.addition::text").get()
            if addition:
                name = f"{title} - {addition.strip()}"
            else:
                name = title

            image = card.css("img.image::attr(src)").get()

            # Parse price
            price = None
            price_main = card.css("div.prices__offer span::text").get()
            price_sub = card.css("div.prices__offer small span::text").get()
            if price_main and price_sub:
                try:
                    price = float(f"{price_main.strip()}.{price_sub.strip()}")
                except ValueError:
                    pass

            if price is None:
                # Try regular price or chip text fallback
                reg_text = card.css("span.regular::text").get()
                if reg_text:
                    try:
                        price = float(reg_text.replace(",", ".").strip())
                    except ValueError:
                        pass

            item = Product(
                name=name,
                website=response.url,
                image=image,
                ref=str(ref),
                sku=str(ref),
                price=price,
                proof_currency="EUR",
                located_in_wikidata="Q2489350",
            )

            if offers_data := card.css("div.prices__offer"):
                item["offers"] = [{
                    "@type": "Offer",
                    "priceCurrency": "EUR",
                    "price": str(price) if price is not None else None,
                    "availability": "https://schema.org/InStock",
                }]

            yield item

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        item["located_in_wikidata"] = "Q2489350"
        item["proof_currency"] = "EUR"

        if not item.get("ref"):
            match = re.search(r"/(\d+)$", response.url)
            if match:
                item["ref"] = match.group(1)
                item["sku"] = match.group(1)

        return item
