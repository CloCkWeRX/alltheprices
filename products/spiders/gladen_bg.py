from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class GladenBGSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Gladen.bg (HIT Max Bulgaria).
    Uses SitemapSpider with StructuredDataSpider to parse product JSON-LD data.
    """

    name = "gladen_bg"
    allowed_domains = ["gladen.bg"]
    sitemap_urls = ["https://gladen.bg/sitemap.xml"]
    sitemap_rules = [(r"/product/([^/]+)$", "parse_sd")]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1.5,
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if "loc" in entry:
                loc = entry["loc"]
                if "sitemap" in loc or "/product/" in loc:
                    yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Resolve relative website URL
        if item.get("website") and not item["website"].startswith("http"):
            item["website"] = response.urljoin(item["website"])

        # Try to extract the actual SKU/ref from the page
        sku = response.xpath('//*[@id="skuDisplay"]/text()').get()
        if sku:
            item["ref"] = sku.strip()
            item["sku"] = sku.strip()
        else:
            try:
                import json
                config_text = response.xpath('//script[@id="product-page-config"]/text()').get()
                if config_text:
                    config_data = json.loads(config_text)
                    sku_from_config = config_data.get("baseVariation", {}).get("sku") or config_data.get("shop_page_data", {}).get("sku")
                    if sku_from_config:
                        item["ref"] = str(sku_from_config).strip()
                        item["sku"] = str(sku_from_config).strip()
            except Exception:
                pass

        if not item.get("ref"):
            # fallback to URL part
            ref = self.get_ref(response.url, response)
            item["ref"] = ref

        # Promotes price and currency from offers to top level fields
        if item.get("offers"):
            offers = item["offers"]
            if isinstance(offers, dict):
                offers = [offers]
                item["offers"] = offers
            if offers:
                offer = offers[0]
                item["price"] = offer.get("price")
                item["proof_currency"] = offer.get("priceCurrency")

        # Clean relative URLs in offers
        for offer in item.get("offers", []):
            if offer.get("url") and isinstance(offer["url"], str) and not offer["url"].startswith("http"):
                offer["url"] = response.urljoin(offer["url"])

        yield item
