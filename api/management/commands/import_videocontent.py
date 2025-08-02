import csv
import os
from django.core.management.base import BaseCommand
from api.models import VideoContent
from django.conf import settings
from django.core.files import File
from django.utils.dateparse import parse_datetime


class Command(BaseCommand):
    help = 'Import VideoContent from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                try:
                    video = VideoContent(
                        title=row['title'],
                        description=row.get('description', ''),
                        uploaded_at=parse_datetime(row['uploaded_at'])
                    )

                    video_path = os.path.join(settings.MEDIA_ROOT, row['video_file'])
                    if os.path.exists(video_path):
                        with open(video_path, 'rb') as vid_file:
                            video.video_file.save(os.path.basename(video_path), File(vid_file), save=False)

                    video.full_clean()
                    video.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Imported: {video.title}"))
                except Exception as e:
                    self.stderr.write(f"✗ Error importing {row.get('title')}: {e}")
