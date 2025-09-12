from django.db import transaction
from django.conf import settings
from collections import Counter
from ..models import Order, OrderItem, OrderItemCharm, CartItem, ReviewToken
# from midtrans_services import create_midtrans_token
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.templatetags.static import static
from io import BytesIO

def generate_invoice_pdf_html(order):
    processed_items = []

    for item in order.items.all():
        base_name, base_price = "", 0

        if item.product:
            base_name = item.product.name
            base_price = item.product.price
        elif item.gift_set:
            base_name = item.gift_set.name
            base_price = item.gift_set.price

        charm_names = []
        charm_total = 0
        for charm_item in item.charms.all():
            if charm_item.charm:
                charm_names.append(charm_item.charm.name)
                charm_total += charm_item.charm.price or 0

        if base_name and charm_names:
            description = f"{base_name} + {', '.join(charm_names)}"
            final_price = base_price + charm_total
        elif base_name:
            description = base_name
            final_price = base_price
        elif charm_names:
            description = ", ".join(charm_names)
            final_price = charm_total
        else:
            description = "Unknown"
            final_price = 0

        row_total = final_price * item.quantity

        processed_items.append({
            "description": description,
            "price": final_price,
            "quantity": item.quantity,
            "total": row_total,
        })

    html_string = render_to_string(
        "invoice/base.html", 
        {"order": order, "processed_items": processed_items}
    )
    css_path = settings.STATIC_ROOT + "/css/style.css"
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file, stylesheets=[CSS(css_path)])
    return pdf_file.getvalue()

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
    review_url = f"https://sparkloreofficial.com/review/{order.billcode}/"
    subject = f"Terima kasih atas pesanan Anda"
        
    message = f"""
Halo {order.user.first_name or order.user.username},

Terima kasih telah memesan di Sparklore!

Berikut adalah detail pesanan Anda:

Total Pembayaran : Rp {order.total_price:,.0f}
Alamat Pengiriman :
{order.shipping_address}
Klik link berikut untuk tracking pesanan Anda: {review_url}

Kami akan segera memproses pesanan Anda.
Terima kasih telah berbelanja bersama kami!

Hormat kami,
Tim Sparklore
"""

    pdf = generate_invoice_pdf_html(order)
    
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
    )
    email.attach(f"Invoice_Order_{order.id}.pdf", pdf, "application/pdf")
    email.send(fail_silently=False)