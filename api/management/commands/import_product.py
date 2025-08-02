import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from api.models import Product
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = 'Import Product from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the product CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    product = Product(
                        name=row['name'],
                        category=row['category'],
                        price=Decimal(row['price']),
                        label=row['label'],
                        rating=Decimal(row.get('rating') or 0),
                        description=row.get('description', ''),
                        details=row.get('details', ''),
                        stock=int(row.get('stock') or 0),
                        created_at=parse_datetime(row.get('created_at')),
                        sold_stok=int(row.get('sold_stok') or 0),
                        discount=Decimal(row.get('discount') or 0),
                        charms=bool(int(row.get('charms', 0))),
                        is_charm_spreadable=bool(int(row.get('is_charm_spreadable', 0))),
                    )

                    product.full_clean()
                    product.save()

                    self.stdout.write(self.style.SUCCESS(f"✓ Imported: {product.name}"))

                except Exception as e:
                    self.stderr.write(f"✗ Error importing {row.get('name')}: {e}")
