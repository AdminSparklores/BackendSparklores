import csv
from django.core.management.base import BaseCommand
from api.models import Charm  # ganti `your_app` dengan nama app kamu
from django.core.files.base import ContentFile
from django.core.files import File
from decimal import Decimal
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Import data charms dari CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    charm = Charm(
                        name=row['name'],
                        category=row['category'],
                        label=row.get('label', 'null'),
                        price=Decimal(row['price']),
                        rating=Decimal(row.get('rating', 0)),
                        description=row.get('description', ''),
                        stock=int(row.get('stock', 0)),
                        sold_stok=int(row.get('sold_stok', 0)),
                        discount=Decimal(row.get('discount', 0)),
                    )

                    # Handle image field as dummy file or leave blank
                    if row.get('image'):
                        image_path = os.path.join(settings.MEDIA_ROOT, 'charms', row['image'])
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as img_file:
                                charm.image.save(row['image'], File(img_file), save=False)

                    charm.full_clean()  # validasi model
                    charm.save()
                    self.stdout.write(self.style.SUCCESS(f"Berhasil menambahkan: {charm.name}"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Gagal menambahkan: {row.get('name')} | Error: {e}"))
