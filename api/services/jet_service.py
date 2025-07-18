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
    ORDER_BASE_URL = "https://demo-ecommerce.inuat-jntexpress.id"
    GENERAL_BASE_URL = "https://demo-general.inuat-jntexpress.id"

    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY")
    midtrans_is_production = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower()

    # Credentials
    ORDER_KEY = ""
    ORDER_USERNAME = ""
    ORDER_API_KEY = ""
    TARIFF_KEY = ""
    TRACK_PASSWORD = ""
    ECOMPANY_ID = ""

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
