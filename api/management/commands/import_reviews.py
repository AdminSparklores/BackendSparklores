import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from api.models import Review, Order
from django.utils.dateparse import parse_datetime
from django.db import transaction


class Command(BaseCommand):
    help = 'Import api_review from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    uploaded_at = parse_datetime(row['uploaded_at'])

                    review = Review(
                        user_name=row['user_name'],
                        user_email=row.get('user_email') or None,
                        rating=int(row['rating']),
                        review_text=row.get('review_text') or '',
                        uploaded_at=uploaded_at,
                    )

                    # Handle foreign key: order
                    if row.get('order_id'):
                        review.order = Order.objects.filter(pk=row['order_id']).first()

                    review.save()

                    # Handle image if exists
                    if row.get('image'):
                        image_path = os.path.join(settings.MEDIA_ROOT, row['image'])
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as img_file:
                                review.image.save(os.path.basename(image_path), File(img_file), save=True)
                        else:
                            self.stdout.write(self.style.WARNING(f"⚠ Gambar tidak ditemukan: {image_path}"))

                    self.stdout.write(self.style.SUCCESS(f"✓ Review dari '{review.user_name}' berhasil diimpor."))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Error pada baris: {row}\n  ↪ {e}"))
