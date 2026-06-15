import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider


class PaodeacucarBRSpider(CrawlSpider, StructuredDataSpider):
    name = "paodeacucar_br"
    allowed_domains = ["paodeacucar.com"]
    start_urls = ["https://www.paodeacucar.com/categoria/alimentos/hortifruti"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3411543",
                "name": "Pão de Açúcar",
            }
        }
    }

    rules = (
        Rule(LinkExtractor(allow=r"/produto/\d+/[\w-]+"), callback="parse_sd"),
        Rule(LinkExtractor(allow=(r"/categoria/[\w-]+", r"/secoes/C\d+/[\w-]+"))),
    )

    def parse_start_url(self, response, **kwargs):
        yield from self.extract_next_data_links(response)

    def parse_sd(self, response, **kwargs):
        yield from self.extract_next_data_links(response)
        yield from super().parse_sd(response)

    def extract_next_data_links(self, response):
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                links = self._find_links(data)
                for link in links:
                    yield response.follow(link)
            except Exception:
                self.logger.exception("Failed to parse __NEXT_DATA__")

    def _find_links(self, obj):
        links = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["uiLink", "link", "urlDetails"] and isinstance(v, str):
                    if v.startswith("/produto/") or v.startswith("/categoria/") or v.startswith("/secoes/"):
                        links.add(v)
                else:
                    links.update(self._find_links(v))
        elif isinstance(obj, list):
            for item in obj:
                links.update(self._find_links(item))
        return links
