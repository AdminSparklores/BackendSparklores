import csv
import os
from django.core.management.base import BaseCommand
from api.models import PhotoGallery
from django.conf import settings
from django.core.files import File
from django.utils.dateparse import parse_datetime


class Command(BaseCommand):
    help = 'Import PhotoGallery from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    pg = PhotoGallery(
                        alt_text=row['alt_text'],
                        description=row.get('description', ''),
                        uploaded_at=parse_datetime(row['uploaded_at'])
                    )

                    image_path = os.path.join(settings.MEDIA_ROOT, row['image'])
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            pg.image.save(os.path.basename(image_path), File(img_file), save=False)

                    pg.full_clean()
                    pg.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Imported: {pg.alt_text}"))
                except Exception as e:
                    self.stderr.write(f"✗ Error importing {row.get('alt_text')}: {e}")
