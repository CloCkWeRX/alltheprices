import re

from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.structured_data_spider import StructuredDataSpider


class ChataPolskaSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Chata Polska (Poland).
    Wikidata: Q89254287

    Sample structured data:
    {
      "extras": {
        "@source_uri": "https://poznankeplera.chatapolska.pl/owoce-i-warzywa/4359-natka-pietruszki-pczek.html",
        "seller": {
          "@type": "Organization",
          "@id": "https://www.wikidata.org/wiki/Q89254287",
          "name": "Chata Polska"
        }
      },
      "name": "Natka pietruszki pęczek",
      "website": "https://poznankeplera.chatapolska.pl/owoce-i-warzywa/4359-natka-pietruszki-pczek.html",
      "image": "https://poznankeplera.chatapolska.pl/22581-medium_default/natka-pietruszki-pczek.jpg",
      "ref": "355",
      "offers": [
        {
          "@type": "Offer",
          "availability": "https://schema.org/InStock",
          "priceCurrency": "PLN",
          "url": "https://poznankeplera.chatapolska.pl/owoce-i-warzywa/4359-natka-pietruszki-pczek.html",
          "price": "2.79"
        }
      ]
    }
    """

    name = "chatapolska"
    allowed_domains = ["chatapolska.pl"]
    start_urls = ["https://sklep.chatapolska.pl/nasze-sklepy"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q89254287",
                "name": "Chata Polska",
            }
        }
    }

    rules = (
        # Process product pages - match this first
        Rule(LinkExtractor(allow=r".*/\d+-[\w-]+\.html$"), callback="parse_sd"),
        # Discover categories on subdomains
        Rule(LinkExtractor(allow=r"https://[a-z0-9]+\.chatapolska\.pl/[a-z0-9-]+/"), follow=True),
    )

    def parse_start_url(self, response, **kwargs):
        # Extract store subdomain links from JavaScript/text
        links = re.findall(r"https://[a-z0-9]+\.chatapolska\.pl/", response.text)
        for link in set(links):
            # Use the default parse method to ensure it goes through CrawlSpider rules
            yield Request(link)

    def get_ref(self, url, response):
        # Extract ID from URL like https://obrzycko.chatapolska.pl/napoje-mleczne/1477-bakoma-men-shake-z-wysoka-zawartoscia-protein-smak-truskawkowy-380-g.html
        if match := re.search(r"/(\d+)-[\w-]+\.html", url):
            return match.group(1)
        return super().get_ref(url, response)
