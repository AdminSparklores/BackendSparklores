from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from ..models import ReviewToken

def create_and_send_review_token(order):
    token, created = ReviewToken.objects.get_or_create(user=order.user, order=order)
    review_url = f"https://sparkloreofficial.com/review/?token={token.token}"
    subject = "Berikan ulasan untuk pesananmu"
    message = f"Halo {order.user.email},\n\nKlik link di bawah untuk memberikan review kepuasan anda terhadap produk kami : {review_url} \n\n Salam Hangat,\nTim Sparklore"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
    return token
