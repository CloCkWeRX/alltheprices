import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class BimTRSpider(CrawlSpider):
    """
    Spider for BİM (Turkey).
    Wikidata: Q1022075
    """
    name = "bim_tr"
    allowed_domains = ["bim.com.tr"]
    start_urls = ["https://www.bim.com.tr/"]

    user_agent = FIREFOX_LATEST

    rules = (
        # Categories
        Rule(LinkExtractor(allow=(r"/Categories/\d+/.*", r"/urunler/.*/categories\.aspx", r"/Markalar/\d+/.*"))),
        # Products
        Rule(LinkExtractor(allow=(r"/aktuel-urunler/.*/aktuel\.aspx", r"/urunler/.*/product\.aspx")), callback="parse_product"),
    )

    def parse_product(self, response):
        item = Product()

        # The product name is typically in .titleArea h2.title
        name = response.css(".titleArea h2.title::text").get()
        if not name:
            # Fallback
            name = response.css("h2.title::text").get()

        if not name:
            return

        item["name"] = name.strip()
        item["website"] = response.url

        image = response.css(".leftSide .imageArea img::attr(src)").get()
        if image:
            item["image"] = response.urljoin(image)

        # Price extraction
        quantify = response.css(".priceArea .quantify::text").get()
        number = response.css(".priceArea .number::text").get()

        if quantify and number:
            # Price format: "399," + "00" -> "399.00"
            # Cleanup quantify: might have dots for thousands separator
            price_str = quantify.replace(".", "").replace(",", "") + "." + number
            item["price"] = price_str
            item["proof_currency"] = "TRY"

        ref = response.css(".shareArea a::attr(data-id)").get()
        if ref:
            item["ref"] = ref
        else:
            # Fallback to URL slug
            match = re.search(r"/([^/]+)/(aktuel|product)\.aspx$", response.url)
            if match:
                item["ref"] = match.group(1)

        item["located_in_wikidata"] = "Q1022075"

        # Limit description to the actual product info area to avoid noise from other products
        description = response.css(".detailArea .textArea ::text").getall()
        if description:
            desc_text = " ".join([d.strip() for d in description if d.strip()])
            if desc_text:
                item["description"] = desc_text

        yield item
