import json
import logging
import re
import traceback

import chompjs
import json5

from products.items import Product

logger = logging.getLogger(__name__)


class LinkedDataParser:
    @staticmethod
    def iter_linked_data(response, json_parser="json"):
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            try:
                if json_parser == "json5":
                    ld_obj = json5.loads(ld)
                elif json_parser == "chompjs":
                    ld_obj = chompjs.parse_js_object(ld)
                else:
                    ld_obj = json.loads(ld, strict=False)
            except (json.decoder.JSONDecodeError, ValueError):
                continue

            if isinstance(ld_obj, dict):
                if "@graph" in ld_obj:
                    yield from filter(None, ld_obj["@graph"])
                else:
                    yield ld_obj
            elif isinstance(ld_obj, list):
                yield from filter(None, ld_obj)
            else:
                raise TypeError(ld_obj)

    @staticmethod
    def find_linked_data(response, wanted_type, json_parser="json") -> {}:
        if isinstance(wanted_type, list):
            wanted_types = [LinkedDataParser.clean_type(t) for t in wanted_type]
        else:
            wanted_types = [LinkedDataParser.clean_type(wanted_type)]

        for ld_obj in LinkedDataParser.iter_linked_data(response, json_parser=json_parser):
            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            if all(wanted in types for wanted in wanted_types):
                return ld_obj

    @staticmethod
    def parse_ld(ld, time_format: str = "%H:%M") -> Product:  # noqa: C901
        item = Product()

        item["name"] = LinkedDataParser.get_case_insensitive(ld, "name")
        if isinstance(item["name"], list):
            item["name"] = item["name"][0]

        item["website"] = LinkedDataParser.get_case_insensitive(ld, "url")

        if image := LinkedDataParser.get_case_insensitive(ld, "image"):
            if isinstance(image, list):
                image = image[0]

            if isinstance(image, str):
                item["image"] = image
            elif isinstance(image, dict):
                if LinkedDataParser.check_type(image.get("@type"), "ImageObject"):
                    item["image"] = LinkedDataParser.get_case_insensitive(image, "contentUrl")

        item["ref"] = LinkedDataParser.get_case_insensitive(ld, "branchCode")
        if item["ref"] is None or item["ref"] == "":
            item["ref"] = LinkedDataParser.get_case_insensitive(ld, "@id")

        if item["ref"] == "":
            item["ref"] = None

        types = ld.get("@type", [])
        if not isinstance(types, list):
            types = [types]
        types = [LinkedDataParser.clean_type(t) for t in types]
        for t in types:
            LinkedDataParser.parse_enhanced(t, ld, item)

        LinkedDataParser.parse_same_as(ld, item)

        return item

    @staticmethod
    def parse(response, wanted_type, json_parser="json") -> Product:
        ld_item = LinkedDataParser.find_linked_data(response, wanted_type, json_parser=json_parser)
        if ld_item:
            item = LinkedDataParser.parse_ld(ld_item)

            if isinstance(item["website"], list):
                item["website"] = item["website"][0]

            if not item["website"]:
                item["website"] = response.url
            elif item["website"].startswith("www"):
                item["website"] = "https://" + item["website"]

            return item

    @staticmethod
    def get_clean(obj, key):
        if value := obj.get(key):
            if isinstance(value, str):
                if value == "null":
                    return None
                return value.strip(" ,")
            return value

    @staticmethod
    def get_case_insensitive(obj, key):
        # Prioritise the case correct key
        if value := LinkedDataParser.get_clean(obj, key):
            return value

        for real_key in obj:
            if real_key.lower() == key.lower():
                return LinkedDataParser.get_clean(obj, real_key)

    @staticmethod
    def check_type(type: str, wanted_type: str, default: bool = True) -> bool:
        if default and type is None:
            return True

        return LinkedDataParser.clean_type(type) == wanted_type.lower()

    @staticmethod
    def clean_type(type: str) -> str:
        return type.lower().replace("http://", "").replace("https://", "").replace("schema.org/", "")

    @staticmethod
    def clean_float(value: str | float) -> float:
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            try:
                return float(value.replace(",", "."))
            except:
                pass
        # Pass the bad data forward and let the validation pipeline complain
        return value

    @staticmethod
    def parse_enhanced(t: str, ld: dict, item: Product):
        if t == "hotel":
            LinkedDataParser.parse_enhanced_hotel(ld, item)

    @staticmethod
    def parse_enhanced_hotel(ld: dict, item: Product):
        if stars := LinkedDataParser.get_case_insensitive(ld, "starRating"):
            if isinstance(stars, str):
                item["extras"]["stars"] = stars
            elif isinstance(stars, dict):
                item["extras"]["stars"] = LinkedDataParser.get_case_insensitive(stars, "ratingValue")

    @staticmethod
    def parse_same_as(ld: dict, item: Product):
        if same_as := LinkedDataParser.get_clean(ld, "sameAs"):
            if isinstance(same_as, str):
                same_as = [same_as]
            for link in same_as:
                if "facebook.com" in link:
                    add_social_media(item, "facebook", link)
