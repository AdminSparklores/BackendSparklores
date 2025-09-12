from celery import shared_task
from django.utils import timezone
from api.models import Order
from api.services import jet_service
import logging

logger = logging.getLogger("celery")

STATUS_MAPPING = {
    "Paket telah diterima": Order.FulfillmentStatus.DELIVERY,
    "Manifes": Order.FulfillmentStatus.PACKING,
    "Paket telah diterima oleh": Order.FulfillmentStatus.SHIPPED,
    "Paket akan dikirim ke alamat penerima": Order.FulfillmentStatus.ON_SHIPPING,
}


def map_status(api_status: str):
    for key, val in STATUS_MAPPING.items():
        if api_status.startswith(key):
            return val
    return None


@shared_task
def update_order_status_from_tracking():
    orders = Order.objects.exclude(billcode__isnull=True).exclude(billcode="")

    for order in orders:
        try:
            resp = jet_service().track(order.billcode)
            history = resp.get("history", [])
            if not history:
                continue

            latest_status = history[-1].get("status", "")
            mapped_status = map_status(latest_status)

            if mapped_status and mapped_status != order.fulfillment_status:
                order.fulfillment_status = mapped_status
                order.updated_at = timezone.now()
                order.save(update_fields=["fulfillment_status", "updated_at"])

        except Exception as e:
            logger.error(f"Failed tracking {order.billcode}: {e}")
