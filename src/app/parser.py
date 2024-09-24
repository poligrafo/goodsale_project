import logging
import uuid
from io import BytesIO
from typing import Any, Dict, Iterator

import requests
from lxml import etree

from src.core.models import SKU
from src.core.schemas import SKUCreate

logger = logging.getLogger(__name__)


class XMLParser:
    def __init__(self, xml_url: str):
        self.xml_url = xml_url
        self.category_map: Dict[str, Any] = {}

    def fetch_xml_stream(self):
        logger.info("Loading an XML stream from %s", self.xml_url)
        response = requests.get(self.xml_url, stream=True)
        response.raise_for_status()
        return response.content

    def parse_categories(self, root):
        logger.info("Category parsing")
        categories = {}
        for category in root.xpath("//categories/category"):
            category_id = category.get("id")
            parent_id = category.get("parentId")
            name = category.text.strip()
            categories[category_id] = {
                "id": category_id,
                "parent_id": parent_id,
                "name": name,
            }

        def build_category_path(cat_id):
            path = []
            while cat_id:
                cat = categories.get(cat_id)
                if not cat:
                    break
                path.insert(0, cat["name"])
                cat_id = cat["parent_id"]
            return path

        for cat_id in categories:
            categories[cat_id]["full_path"] = build_category_path(cat_id)

        self.category_map = categories

    def parse(self) -> Iterator[SKU]:
        xml_content = self.fetch_xml_stream()
        xml_file = BytesIO(xml_content)
        context = etree.iterparse(
            source=xml_file,
            events=("end",),
            tag=("offer", "categories"),
            recover=True,
        )

        for event, elem in context:
            if elem.tag == "categories":
                self.parse_categories(elem)
                elem.clear()
                continue

            if elem.tag == "offer":
                try:
                    sku = self.parse_offer(elem)
                    yield sku
                except Exception as e:
                    logger.error("Error when parsing a sentence: %s", e)
                finally:
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]

        xml_file.close()

    def parse_offer(self, elem) -> SKU:
        sku_data = {
            "marketplace_id": 1,
            "product_id": int(elem.get("id")),
            "title": elem.findtext("name"),
            "description": elem.findtext("description"),
            "brand": elem.findtext("vendor"),
            "seller_id": None,
            "seller_name": elem.findtext("vendorCode"),
            "first_image_url": elem.findtext("picture"),
            "category_id": int(elem.findtext("categoryId")),
            "features": {},
            "price_before_discounts": float(
                elem.findtext("oldprice") or elem.findtext("price")
            ),
            "price_after_discounts": float(elem.findtext("price")),
            "currency": elem.findtext("currencyId"),
            "barcode": elem.findtext("barcode"),
            "rating_count": None,
            "rating_value": None,
            "discount": None,
        }

        if sku_data["price_before_discounts"] and sku_data["price_after_discounts"]:
            sku_data["discount"] = (
                (sku_data["price_before_discounts"] - sku_data["price_after_discounts"])
                / sku_data["price_before_discounts"]
                * 100
            )

        category_id = str(sku_data["category_id"])
        category_info = self.category_map.get(category_id, {})
        full_path = category_info.get("full_path", [])
        sku_data["category_lvl_1"] = full_path[0] if len(full_path) > 0 else None
        sku_data["category_lvl_2"] = full_path[1] if len(full_path) > 1 else None
        sku_data["category_lvl_3"] = full_path[2] if len(full_path) > 2 else None
        sku_data["category_remaining"] = (
            "/".join(full_path[3:]) if len(full_path) > 3 else None
        )

        parameters = {}
        for param in elem.findall("param"):
            param_name = param.get("name")
            param_value = param.text
            parameters[param_name] = param_value
        sku_data["features"] = parameters

        sku_uuid = uuid.uuid4()

        sku_create = SKUCreate(**sku_data)
        sku = SKU(**sku_create.dict())
        sku.uuid = sku_uuid

        return sku
