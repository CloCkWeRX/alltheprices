# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import logging
from datetime import datetime
from enum import Enum
from typing import Iterable

import scrapy

logger = logging.getLogger(__name__)


class Product(scrapy.Item):
    name = scrapy.Field()
    website = scrapy.Field()
    image = scrapy.Field()
    ref = scrapy.Field()
    gtin = scrapy.Field()
    gtin12 = scrapy.Field()
    gtin13 = scrapy.Field()
    sku = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    located_in = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    offers = scrapy.Field()
    extras = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._values.get("extras"):
            self.__setitem__("extras", {})


# def merge_items(language_dict: dict, main_language: str, matching_key: str = "ref") -> Iterable[Product]:
#     """
#     Merge multiple items in different languages together. See starbucks_cn for example usage.
#     :param language_dict: a dict of language to a dict of keys to items for all of the languages/items to be merged.
#     :param main_language: the language to be used for the main keys in the item.
#     :param matching_key: the key (defaults to "ref") that is used to match up items from different languages.
#     :return: individual merged items
#     """
#     all_item_refs = {language: [ref for ref in items.keys()] for language, items in language_dict.items()}
#     for item in language_dict[main_language].values():
#         matched_items = {}
#         for language, items in language_dict.items():
#             if item[matching_key] in items.keys():
#                 matched_items[language] = items[item[matching_key]]
#                 all_item_refs[language].remove(item[matching_key])
#             else:
#                 logger.warning(
#                     f"No matches found for '{matching_key}': '{item[matching_key]}' in language '{language}'"
#                 )

#         item = get_merged_item(matched_items, main_language)
#         yield item
#     for language, refs in all_item_refs.items():
#         if len(refs) > 0:
#             logger.warning(f"Failed to match {len(refs)} for language: {language}")
#         for ref in refs:
#             yield language_dict[language][ref]


KEYS_THAT_SHOULD_MATCH = [
    "image",
    "ref",
    "brand",
    "brand_wikidata",
]

TRANSLATABLE_EXTRA_KEYS = [
]

TRANSLATABLE_PREFIXES = [
]


def get_merged_item(matched_items: dict, main_language: str) -> dict:
    """
    Merge items in different languages, but which are the same product, together.
    :param matched_items: a dict of language to item for all of the languages/items to be merged.
    :param main_language: the language to be used for the main keys in the item.
    :return: a single merged item
    """
    # Do extras first before we add language keys to it
    item = get_merged_extras(matched_items, main_language)

    all_keys = set([key for match in matched_items.values() for key in match.keys()])
    for key, value in {key: item.get(key) for key in all_keys}.items():
        if key == "extras":
            continue
        if all([value == match.get(key) for match in matched_items.values()]):
            continue

        if key in KEYS_THAT_SHOULD_MATCH:
            logger.warning(f"Key '{key}' does not match in all items for ref: {item['ref']}")
        for language, match in matched_items.items():
            item["extras"][f"{key}:{language}"] = match.get(key)
    return item


def get_merged_extras(matched_items: dict, main_language: str) -> dict:
    item = matched_items[main_language]
    extras_keys = set([key for match in matched_items.values() for key in match["extras"].keys()])
    for extras_key, extras_value in {key: item["extras"].get(key) for key in extras_keys}.items():
        if all([extras_value == match["extras"].get(extras_key) for match in matched_items.values()]):
            continue
        if extras_key in TRANSLATABLE_EXTRA_KEYS:
            for language, match in matched_items.items():
                item["extras"][f"{extras_key}:{language}"] = match["extras"].get(extras_key)
        for prefix in TRANSLATABLE_PREFIXES:
            if extras_key.startswith(prefix):
                for language, match in matched_items.items():
                    item["extras"][f"{extras_key}:{language}"] = match["extras"].get(extras_key)
    return item