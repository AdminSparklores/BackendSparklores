# import requests
# from django.conf import settings

# class MidtransService:
#     base_url = 'https://api.midtrans.com/v2'
#     auth = (settings.MIDTRANS_SERVER_KEY, '')

#     @classmethod
#     def create_transaction(cls, order_id, amount, payment_type, **kwargs):
#         payload = {
#             'transaction_details': {'order_id': order_id,'gross_amount': amount},
#             'payment_type': payment_type,
#             **kwargs
#         }
#         resp = requests.post(f'{cls.base_url}/charge', json=payload, auth=cls.auth)
#         return resp.json()

# class RajaOngkirService:
#     url = 'https://api.rajaongkir.com/starter'
#     headers = {'key': settings.RAJA_ONGKIR_KEY, 'Content-Type':'application/json'}

#     @classmethod
#     def estimate_cost(cls, origin, destination, weight, courier):
#         data = {'origin':origin,'destination':destination,'weight':weight,'courier':courier}
#         return requests.post(f'{cls.url}/cost', json=data, headers=cls.headers).json()

#     @classmethod
#     def create_shipment(cls, order_id, origin, destination, weight, courier):
#         # stub; RajaOngkir tidak sediakan create resi via API starter
#         return {'status':'OK','resi':'JNE1234567890'}