import csv
import os
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files import File
from api.models import Charm


class Command(BaseCommand):
    help = 'Import data charms dari CSV dengan validasi dan logging'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path ke file CSV')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        log_file_path = 'import_charms_log.txt'

        with open(log_file_path, 'w', encoding='utf-8') as logfile, open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count_success = 0
            count_fail = 0

            for row in reader:
                try:
                    price_str = row.get('price', '0').replace(',', '').strip()
                    discount_str = row.get('discount', '0').strip()
                    rating_str = row.get('rating', '0').strip()

                    charm = Charm(
                        name=row['name'].strip(),
                        category=row['category'].strip(),
                        label=row.get('label', 'null').strip(),
                        price=Decimal(price_str),
                        rating=Decimal(rating_str),
                        description=row.get('description', '').strip(),
                        stock=int(float(row.get('stock', 0))),
                        sold_stok=int(float(row.get('sold_stok', 0))),
                        discount=Decimal(discount_str),
                    )

                    # Handle image
                    if row.get('image'):
                        image_rel_path = row['image'].strip()
                        image_path = os.path.join(settings.MEDIA_ROOT, image_rel_path)
                        if os.path.exists(image_path):
                            with open(image_path, 'rb') as img_file:
                                charm.image.save(os.path.basename(image_path), File(img_file), save=False)
                        else:
                            logfile.write(f"[WARN] Gambar tidak ditemukan: {image_path}\n")

                    charm.full_clean()
                    charm.save()
                    count_success += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {charm.name} berhasil dimasukkan"))
                except Exception as e:
                    count_fail += 1
                    error_msg = f"[FAIL] {row.get('name', 'UNKNOWN')} | Error: {e}\n"
                    logfile.write(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

            summary = f"\nImport selesai: {count_success} sukses, {count_fail} gagal.\nLog: {log_file_path}"
            self.stdout.write(self.style.SUCCESS(summary))
            logfile.write(summary)
