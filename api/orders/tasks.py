from celery import shared_task
from django.utils import timezone
from api.models import Order
from api.services.jet_service import JetService
import logging

logger = logging.getLogger("celery")

STATUS_MAPPING = {
    "Manifes": Order.FulfillmentStatus.PACKING,

    "Cancelled": Order.FulfillmentStatus.CANCELLED,
    "Cancelled AWB": Order.FulfillmentStatus.CANCELLED,
    "Cancelled AWB by Seller": Order.FulfillmentStatus.CANCELLED,
    "Cancelled AWB by J&T": Order.FulfillmentStatus.CANCELLED,

    "Paket telah diterima oleh": Order.FulfillmentStatus.SHIPPED,

    "Paket akan dikirimkan ke": Order.FulfillmentStatus.ON_SHIPPING,
    "Paket telah dikirimkan ke": Order.FulfillmentStatus.ON_SHIPPING,
    "Paket telah sampai di": Order.FulfillmentStatus.ON_SHIPPING,

    "Paket akan dikirim ke alamat penerima": Order.FulfillmentStatus.DELIVERY,

}

def map_status(api_status: str):
    for key, val in STATUS_MAPPING.items():
        if api_status.startswith(key):
            return val
    return None


@shared_task
def update_order_status_from_tracking():
    """
    Jalankan tiap 5 menit:
      * Ambil order yang punya billcode
      * Bukan fulfillment_status = awaiting_shipment
      * Hit API JNT track
      * Update status sesuai mapping
    """
    orders = (
        Order.objects
        .exclude(billcode__isnull=True)
        .exclude(billcode="")
        .exclude(fulfillment_status=Order.FulfillmentStatus.AWAITING_SHIPMENT)
    )

    for order in orders:
        try:
            resp = JetService().track(order.billcode)
            history = resp.get("history", [])
            if not history:
                continue

            latest_status = history[-1].get("status", "")
            mapped_status = map_status(latest_status)

            if mapped_status and mapped_status != order.fulfillment_status:
                order.fulfillment_status = mapped_status
                order.updated_at = timezone.now()
                order.save(update_fields=["fulfillment_status", "updated_at"])
                logger.info(
                    f"Order {order.id} updated to {mapped_status} "
                    f"from '{latest_status}'"
                )
        except Exception as e:
            logger.error(f"Failed tracking {order.billcode}: {e}")
