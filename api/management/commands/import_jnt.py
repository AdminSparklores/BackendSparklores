from django.core.management.base import BaseCommand
import csv
from api.models import JNTLocation

class Command(BaseCommand):
    help = 'Import JNTLocation from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                JNTLocation.objects.create(
                    provinsi=row['provinsi'],
                    kabupaten_kota=row['kabupaten_kota'],
                    kecamatan=row['kecamatan'],
                    provinsi_jnt=row['provinsi_jnt'],
                    kota_jnt=row['kota_jnt'],
                    kode_kota_jnt=row['kode_kota_jnt'],
                    kecamatan_jnt=row['kecamatan_jnt'],
                    kode_jnt_receiver_area=row['kode_jnt_receiver_area'],
                    notes=row.get('notes', '')
                )
        self.stdout.write(self.style.SUCCESS('Import completed!'))
