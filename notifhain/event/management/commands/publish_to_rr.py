from django.core.management.base import BaseCommand

from notifhain.event.publisher import PublishToRR


class Command(BaseCommand):

    def add_arguments(self, parser):
            # Named (optional) arguments
            parser.add_argument(
                '--do_submit', action='store_true', dest='do_submit',
                help='Do not submit the post. This is for debugging and testing the publisher.',
            )

    def handle(self, *args, **options):
        # post possible new klubnacht timetable to RR
        publisher = PublishToRR()
        publisher.publish(do_submit=options["do_submit"])
