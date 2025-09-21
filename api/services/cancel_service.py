from django.core.mail import EmailMessage
from django.conf import settings

def send_order_cancellation_email(order, reason: str):
    """
    Kirim email pembatalan pesanan ke user.
    :param order: instance Order
    :param reason: alasan pembatalan
    """
    subject = "Pesanan Sparklore Anda Telah Dibatalkan"

    message = f"""
Halo {order.user.first_name or order.user.username or order.user.email},

Kami menyesal memberitahukan bahwa pesanan terbaru Anda dengan nomor
#{order.id} telah dibatalkan karena {reason}.

Untuk memproses pengembalian dana, silakan balas langsung email ini dengan informasi berikut:

1. Nama Lengkap (sesuai metode pembayaran yang digunakan)
2. Nomor Rekening / Detail Pembayaran
3. Nama Bank (jika ada)
4. Nomor Kontak (untuk konfirmasi bila diperlukan)

Setelah kami menerima data tersebut, kami akan memulai proses pengembalian dana secepat mungkin.
Pengembalian dana biasanya selesai dalam waktu 3 hari kerja, tergantung penyedia layanan pembayaran Anda.

Kami mohon maaf atas ketidaknyamanan ini dan berterima kasih atas pengertian Anda.
Jika ada pertanyaan lebih lanjut, jangan ragu untuk membalas email ini.

Salam hangat,
Tim Sparklore
"""

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
    )
    email.send(fail_silently=False)
