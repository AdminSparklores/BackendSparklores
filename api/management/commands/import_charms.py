import csv
import pandas as pd
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from api.models import Charm
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Import data from CSV or XLSX to Charm model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def clean_decimal(self, value):
        """Bersihkan string dan konversi ke Decimal"""
        try:
            if pd.isna(value):
                return Decimal('0.00')
            return Decimal(str(value).replace(',', ''))
        except InvalidOperation:
            self.stderr.write(self.style.ERROR(f"Gagal konversi Decimal: {value}"))
            return Decimal('0.00')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        # Pilih pembaca file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                self.stderr.write("File harus berupa .csv atau .xlsx")
                return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error saat membaca file: {e}"))
            return

        for index, row in df.iterrows():
            try:
                charm, created = Charm.objects.get_or_create(
                    name=row['name'],
                    category=row['category'],
                    defaults={
                        'image': row.get('image', ''),
                        'label': row.get('label', ''),
                        'price': self.clean_decimal(row.get('price')),
                        'rating': self.clean_decimal(row.get('rating')),
                        'description': row.get('description', ''),
                        'stock': int(row.get('stock', 0)),
                        'sold_stok': int(row.get('sold_stok', 0)),
                        'discount': self.clean_decimal(row.get('discount')),
                        'created_at': now()
                    }
                )
                action = "Created" if created else "Skipped"
                self.stdout.write(self.style.SUCCESS(f"{action}: {charm.name}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Gagal impor baris {index + 2}: {e}"))
