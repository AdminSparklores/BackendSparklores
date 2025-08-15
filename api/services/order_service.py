from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from collections import Counter
from ..models import Order, OrderItem, OrderItemCharm, CartItem, ReviewToken
# from midtrans_services import create_midtrans_token

@transaction.atomic
def create_order(user, shipping_address, cart_items):
    if not cart_items.exists():
        raise ValueError("Cart is empty")

    order = Order.objects.create(
        user=user,
        payment_status='pending',
        fulfillment_status='awaiting_shipment',
        total_price=0,
        shipping_address=shipping_address
    )

    total = 0
    for item in cart_items:
        order_item = OrderItem.objects.create(
            order=order,
            product=item.product,
            gift_set=item.gift_set,
            quantity=item.quantity,
            message=item.message
        )

        # Kurangi stok
        if item.product:
            item.product.stock -= item.quantity
            item.product.save()
            total += float(item.product.price) * item.quantity

        elif item.gift_set:
            item.gift_set.stock -= item.quantity
            item.gift_set.save()
            total += float(item.gift_set.price) * item.quantity

        # Tambah charms
        for cc in item.charms.all():
            OrderItemCharm.objects.create(order_item=order_item, charm=cc)
            total += float(cc.price)

        # Hapus cart item
        item.delete()

    order.total_price = total
    order.save()

    # Buat token midtrans
    # midtrans_token = create_midtrans_token(order)
    
    # Buat review token & kirim email
    send_order_confirmation_email(order)

    return order, midtrans_token

def send_order_confirmation_email(order):
    subject = f"Terima kasih atas pesanan Anda"
        
    message = f"""
Halo {order.user.first_name or order.user.username},

Terima kasih telah memesan di Sparklore!

Berikut adalah detail pesanan Anda:

Nomor Pesanan : #{order.id}
Total Pembayaran : Rp {order.total_price:,.0f}
Alamat Pengiriman :
{order.shipping_address}

Kami akan segera memproses pesanan Anda.
Terima kasih telah berbelanja bersama kami!

Hormat kami,
Tim Sparklore
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        fail_silently=False
    )