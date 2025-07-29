import requests
import base64
import json
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

class JetService:
    """
    Service untuk integrasi dengan J&T sandbox.
    Payload & signature dikelola otomatis di sini.
    """
    # Base URLs
    ORDER_BASE_URL = os.getenv("JNT_EXPRESS_ORDER_BASE_URL", "")
    GENERAL_BASE_URL = os.getenv("JNT_EXPRESS_GENERAL_BASE_URL", "")

    # Credentials
    ORDER_KEY = os.getenv("JNT_EXPRESS_ORDER_KEY", "")
    ORDER_USERNAME = os.getenv("JNT_EXPRESS_ORDER_USERNAME", "")
    ORDER_API_KEY = os.getenv("JNT_EXPRESS_ORDER_API_KEY", "")
    TARIFF_KEY = os.getenv("JNT_EXPRESS_TARIF_KEY", "")
    TRACK_PASSWORD = os.getenv("JNT_EXPRESS_TRACK_PASSWORD", "")
    ECOMPANY_ID = os.getenv("JNT_EXPRESS_ECOMPANY_ID", "")

    def _basic_auth_header(self):
        token = f"{self.ECOMPANY_ID}:{self.TRACK_PASSWORD}"
        b64_token = base64.b64encode(token.encode()).decode()
        return f"Basic {b64_token}"

    def _generate_signature(self, data: dict, key: str) -> str:
        """
        Hitung signature: base64(md5(json(data) + key))
        """
        data_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        raw = data_json + key
        print(raw, "\n")

        md5_hex = hashlib.md5(raw.encode()).hexdigest()
        print(md5_hex, "\n")

        b64_encoded = base64.b64encode(md5_hex.encode()).decode()
        
        print(f"Base64 encoded signature: {b64_encoded}")  
        print(f"Data JSON: {data_json}") 
        return data_json, b64_encoded

    def order(self, detail: dict):
        """
        Create order
        """
        url = f"{self.ORDER_BASE_URL}/jts-idn-ecommerce-api/api/order/create"
        wrapper = {"detail": [detail]}
        data_json, data_sign = self._generate_signature(wrapper, self.ORDER_KEY)

        payload = {
            "data_param": data_json,
            "data_sign": data_sign
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def cancel_order(self, detail: dict):
        """
        Cancel order
        :param detail: dict, payload 'detail' saja, tanpa wrapper
        """
        url = f"{self.ORDER_BASE_URL}/jts-idn-ecommerce-api/api/order/cancel"
        wrapper = {"detail": [detail]}
        data_json, data_sign = self._generate_signature(wrapper, self.ORDER_KEY)

        payload = {
            "data_param": data_json,
            "data_sign": data_sign
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def track(self, awb: str):
        """
        Tracking by AWB
        """
        url = f"{self.GENERAL_BASE_URL}/jandt_track/track/trackAction!tracking.action"
        payload = {
            "awb": awb,
            "eccompanyid": self.ECOMPANY_ID
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._basic_auth_header()
        }

        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def tariff_check(self, data: dict):
        """
        Tariff check
        :param data: dict, payload data sesuai API
        """
        url = f"{self.GENERAL_BASE_URL}/jandt_track/inquiry.action"
        data_json, sign = self._generate_signature(data, self.TARIFF_KEY)

        payload = {
            "data": data_json,
            "sign": sign
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def print_waybill(self, billcode: str, printmode: str = "1", print_type: str = "1") -> dict:
        """
        Generate waybill print link.
        :param billcode: AWB number
        :param printmode: Default "1" = single print link
        :param print_type: Default "1"
        """
        url = f"{self.GENERAL_BASE_URL}/jandt_order_web/labels/labelsAction!getPrintUrl.action"

        data = {
            "customerid": self.ECOMPANY_ID,
            "billcode": billcode,
            "printmode": printmode,
            "printType": print_type
        }

        data_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        raw = data_json + self.TRACK_PASSWORD
        md5_hash = hashlib.md5(raw.encode()).digest()
        data_digest = base64.b64encode(md5_hash).decode()

        payload = {
            "logistics_interface": data_json,
            "data_digest": data_digest,
            "msg_type": "ROTAPRINT",
            "eccompanyid": self.ECOMPANY_ID
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        print("===== DEBUG PRINT WAYBILL J&T =====")
        print("Endpoint:", url)
        print("logistics_interface:", data_json)
        print("data_digest:", data_digest)
        print("msg_type:", "ROTAPRINT")
        print("eccompanyid:", self.ECOMPANY_ID)
        print("============================")

        resp = requests.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()
