import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Product, ProductImage
from django.core.files import File

class Command(BaseCommand):
    help = 'Import Product Images from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    product_id = int(row['product_id'])
                    image_path = row['image_path']
                    alt_text = row.get('alt_text', '')

                    product = Product.objects.get(id=product_id)

                    full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

                    if not os.path.exists(full_image_path):
                        self.stderr.write(f"✗ File not found: {full_image_path}")
                        continue

                    with open(full_image_path, 'rb') as image_file:
                        product_image = ProductImage(
                            product=product,
                            alt_text=alt_text
                        )
                        product_image.image.save(os.path.basename(full_image_path), File(image_file), save=False)
                        product_image.full_clean()
                        product_image.save()

                    self.stdout.write(self.style.SUCCESS(f"✓ Added image for product {product.name}"))

                except Product.DoesNotExist:
                    self.stderr.write(f"✗ Product with ID {row['product_id']} not found.")
                except Exception as e:
                    self.stderr.write(f"✗ Error processing image for product ID {row['product_id']}: {e}")
