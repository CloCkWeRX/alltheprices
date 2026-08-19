import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class NormaDESpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for NORMA (Germany/Austria/Czech Republic).
    Wikidata: Q450180
    Fixes #456.
    """
    name = "norma_de"
    allowed_domains = ["norma-online.de"]
    start_urls = ["https://www.norma-online.de/de/angebote/"]

    item_attributes = {
        "located_in_wikidata": "Q450180",
        "brand_wikidata": "Q450180",
        "proof_currency": "EUR",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q450180",
                "name": "NORMA",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 1,
    }

    rules = (
        # Product pages
        # Match URL patterns like /de/angebote/ab-mittwoch,-12.08.26/mittwochs-clou-t-380153/saltletts-i-380913/
        Rule(LinkExtractor(allow=r"/de/angebote/.*-i-(\d+)/$"), callback="parse_product"),
        # Category pages / general overview pages to crawl through
        Rule(LinkExtractor(allow=(r"/de/angebote/ab-[^/]+/$", r"/de/angebote/.*-t-\d+/$"))),
    )

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Name extraction
        name = response.css("#Artikel::text").get()
        if not name:
            name = response.css("div.main h3::text").get()
        if not name:
            name = response.css("h1.headline::text").get()
        if name:
            product["name"] = name.strip()

        # Brand extraction
        brand = response.css("strong.supplier::text").get()
        if brand:
            product["brand"] = brand.strip()

        # Price extraction: e.g. "1,49"
        price_raw = response.css(".produktBox-cont-wrapper-price span::text").get()
        if not price_raw:
            price_raw = response.css(".produktBox-cont-wrapper-price::text").get()
        if price_raw:
            # Clean non-digit characters except comma and dot
            price_clean = re.sub(r"[^\d,.]", "", price_raw)
            # Replace comma with dot
            price_clean = price_clean.replace(",", ".")
            try:
                product["price"] = float(price_clean)
            except ValueError:
                self.logger.warning(f"Could not parse price: {price_raw} from {response.url}")

        # Image extraction
        image = response.css("#js-imgDetail::attr(src)").get()
        if not image:
            image = response.css(".js-imgPreview img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        # Ref extraction from URL (-i-(\d+)/)
        match = re.search(r"-i-(\d+)/", response.url)
        if match:
            product["ref"] = match.group(1)

        yield from self.post_process_item(product, response, {})
