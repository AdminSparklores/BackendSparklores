import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from decimal import Decimal
from django.utils.dateparse import parse_datetime
from django.db import transaction
from api.models import GiftSetOrBundleMonthlySpecial, Product


class Command(BaseCommand):
    help = 'Import GiftSetOrBundleMonthlySpecial from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    gift = GiftSetOrBundleMonthlySpecial(
                        name=row['name'],
                        label=row.get('label', 'null'),
                        description=row.get('description', ''),
                        price=Decimal(row['price']),
                        stock=int(row.get('stock', 0)),
                        sold_stok=int(row.get('sold_stok', 0)),
                        discount=Decimal(row.get('discount', 0)),
                        is_monthly_special=row.get('is_monthly_special', 'True').lower() in ['true', '1']
                    )

                    gift.save()  # Simpan dulu agar bisa tambahkan M2M

                    # Tangani relasi product
                    product_ids = row.get('products', '')
                    for pid in product_ids.split('|'):
                        if pid.strip():
                            product = Product.objects.filter(pk=int(pid)).first()
                            if product:
                                gift.products.add(product)

                    # Tangani gambar
                    image_path = os.path.join(settings.MEDIA_ROOT, row['image'])
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            gift.image.save(os.path.basename(image_path), File(img_file), save=True)
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠ Gambar tidak ditemukan: {image_path}"))

                    self.stdout.write(self.style.SUCCESS(f"✓ GiftSet '{gift.name}' berhasil diimpor."))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"✗ Error pada baris {row.get('name', '')}: {e}"))
