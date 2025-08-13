# services/midtrans_service.py
import midtransclient
import os

def create_midtrans_token(order):
    midtrans_server_key = os.getenv("MIDTRANS_SERVER_KEY")
    midtrans_is_production = os.getenv("MIDTRANS_IS_PRODUCTION", "False").lower() == "true"

    snap = midtransclient.Snap(
        is_production=midtrans_is_production,
        server_key=midtrans_server_key
    )

    param = {
        "transaction_details": {
            "order_id": f"ORDER-{order.id}",
            "gross_amount": float(order.total_price)
        },
        "customer_details": {
            "first_name": order.user.email.split('@')[0],
            "email": order.user.email,
            "shipping_address": {
                "address": order.shipping_address
            }
        }
    }

    transaction = snap.create_transaction(param)
    return {
        'token': transaction['token'],
        'redirect_url': transaction['redirect_url']
    }
