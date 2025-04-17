from scrapy import Spider
from scrapy.http import Response

from products.open_graph_parser import OpenGraphParser


class OpenGraphSpider(Spider):
    dataset_attributes = {"source": "open_graph"}
    wanted_types = ["product"]

    def parse(self, response: Response, **kwargs):
        yield from self.parse_og(response)

    def parse_og(self, response: Response):  # noqa: C901
        og = OpenGraphParser()
        properties = og.extract_properties(response)
        if "type" in properties:
            if properties["type"] in self.wanted_types:
                item = og.as_item(properties, response)
                yield from self.post_process_item(item, response) or []

    def post_process_item(self, item, response, **kwargs):
        """Override with any post-processing on the item."""
        yield item