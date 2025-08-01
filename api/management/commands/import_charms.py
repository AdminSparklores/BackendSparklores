import csv
import pandas as pd
from django.core.management.base import BaseCommand
from api.models import Charm
from django.utils.timezone import now

class Command(BaseCommand):
    help = 'Import data from CSV or XLSX to Charm model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            self.stderr.write("File harus berupa .csv atau .xlsx")
            return

        for index, row in df.iterrows():
            charm, created = Charm.objects.get_or_create(
                name=row['name'],
                category=row['category'],
                defaults={
                    'image': row['image'],
                    'label': row['label'],
                    'price': row['price'],
                    'rating': row['rating'],
                    'description': row['description'],
                    'stock': row['stock'],
                    'sold_stok': row['sold_stok'],
                    'discount': row['discount'],
                    'created_at': now()
                }
            )
            action = "Created" if created else "Skipped"
            self.stdout.write(f"{action}: {charm}")
