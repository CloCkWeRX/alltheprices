import json
import logging
import re
from scrapy import Request, Spider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

logger = logging.getLogger(__name__)


class AmartTWSpider(Spider):
    """
    Spider for A.mart (Taiwan) (Q4648764).
    Crawls products directly via friDay shopping's public API.
    Fix #463.
    """

    name = "amart_tw"
    allowed_domains = [
        "friday.tw",
        "ysdt.com.tw",
        "shopping.friday.tw",
        "k8aiapi.shopping.friday.tw",
        "frontend-gateway.shopping.friday.tw",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q4648764",
    }

    COMMON_BRANDS = [
        "大同",
        "台糖",
        "白蘭氏",
        "飛利浦",
        "幫寶適",
        "靠得住",
        "五木",
        "華陀",
        "禾聯",
        "美心",
        "奇華",
        "佳麗寶",
        "雪花秀",
        "資生堂",
        "理膚寶水",
        "任天堂",
        "三洋",
        "微星",
        "華碩",
        "宏碁",
        "舒潔",
        "蒲公英",
        "春風",
        "五月花",
        "倍潔雅",
        "舒酸定",
        "黑人",
        "高露潔",
        "多芬",
        "麗仕",
        "原萃",
        "光泉",
        "統一",
        "義美",
        "桂格",
        "可口可樂",
        "悅氏",
        "金牌",
        "茶裏王",
        "御茶園",
    ]

    def start_requests(self):
        self.logger.info("Starting A.mart TW API spider...")
        # A.mart store ID is "BW067863"
        payload = {
            "q1_x": 0.5,
            "supplier_y": 1,
            "type": 2,
            "site_id": "BW067863",
            "filter": {
                "k": "1100000000",
                "v": [
                    "243",
                    "45847,46728,46702,47068,25296,47706,47201,48620,46352,43913,48660,42464,45845,45982,46139,46200,46664,46201,46252,46287,47978,48107,48252,48248,48287,25036,45974,46329,46112,46199,47071,48645,48230,45590,23677,44834,43669,46041,46703,46416,46285,48245,45815,24716,45534,46254,46316,46698,46628,47058,47858,48242,48557,48748,48822",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ],
            },
            "list_num": 10000,
        }

        yield Request(
            url="https://k8aiapi.shopping.friday.tw/api/getalist",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload),
            callback=self.parse_getalist,
            dont_filter=True,
        )

    def parse_getalist(self, response):
        self.logger.info("Successfully retrieved A.mart product list from getalist API.")
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse A.mart list response: {e}")
            return

        if not data or not isinstance(data, list):
            return

        pids = []
        for group in data:
            if "pids" in group:
                for item in group["pids"]:
                    # Only parse products belonging to A.mart (supplier ID 243)
                    if item.get("supplier_id") == 243:
                        pids.append(item["pid"])

        self.logger.info(f"Discovered {len(pids)} A.mart product IDs. Fetching details in batches...")

        # Batch them into chunks of 200 to fetch details
        chunk_size = 200
        for i in range(0, len(pids), chunk_size):
            chunk = pids[i : i + chunk_size]
            payload = {"param": {"productIdList": chunk, "type": 1, "isPrimary": True}}
            yield Request(
                url="https://frontend-gateway.shopping.friday.tw/frontendapi/product/v3/productinfo",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps(payload),
                callback=self.parse_productinfo,
                dont_filter=True,
            )

    def extract_brand(self, name: str) -> str:
        # Remove leading brackets
        name = re.sub(r"^[【\[].*?[】\]]\s*", "", name)
        name = re.sub(r"【愛買】$", "", name)
        name = re.sub(r"【愛買嚴選】$", "", name)
        name = name.strip()

        # 1. Match leading English brand names (alphanumeric/hyphen)
        m_eng = re.match(r"^([A-Za-z0-9\-]+)", name)
        if m_eng:
            eng_brand = m_eng.group(1).strip()
            if len(eng_brand) > 1 and not eng_brand.isdigit():
                return eng_brand

        # 2. Match common Chinese brand names
        for brand in self.COMMON_BRANDS:
            if name.startswith(brand):
                return brand

        # 3. Fallback: first 2-4 characters if they are Chinese
        m_chi = re.match(r"^([\u4e00-\u9fa5]{2,4})", name)
        if m_chi:
            val = m_chi.group(1)
            if val not in ["特級", "優質", "嚴選", "精選", "含運", "快速", "美味"]:
                return val

        return "愛買"

    def parse_productinfo(self, response):
        self.logger.info("Successfully retrieved productinfo details batch.")
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse A.mart productinfo response: {e}")
            return

        if not data or data.get("resultCode") != 0:
            return

        products_data = data.get("resultData", [])
        for p in products_data:
            pid = p.get("nPid")
            if not pid:
                continue

            name = p.get("name")
            image_url = p.get("images")

            # Construct standard product detail URL
            product_url = f"https://ec-w.shopping.friday.tw/product/{pid}"

            # Pricing
            price = p.get("memberPrice")
            market_price = p.get("marketPrice")

            if price is not None:
                price = float(price)

            price_is_discounted = False
            price_without_discount = None
            if price and market_price and float(price) < float(market_price):
                price_is_discounted = True
                price_without_discount = float(market_price)

            brand = self.extract_brand(name)

            product = Product(
                name=name,
                website=product_url,
                ref=str(pid),
                sku=p.get("skuId") or str(pid),
                image=image_url,
                brand=brand,
                price=price,
                price_is_discounted=price_is_discounted,
                price_without_discount=price_without_discount,
                proof_currency="TWD",
                located_in_wikidata="Q4648764",
            )

            product["extras"] = {
                "seller": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q4648764",
                    "name": "愛買",
                }
            }

            yield product
