from django.core.management.base import BaseCommand

from notifhain.event.publisher import PublishToRR


class Command(BaseCommand):

    def handle(self, *args, **options):
        # post possible new klubnacht timetable to RR
        publisher = PublishToRR()
        publisher.publish()
