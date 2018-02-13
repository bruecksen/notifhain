from notifhain.event.models import Program, DancefloorEvent, DancefloorEventDetails, \
    Room, Slot

from scrapy_djangoitem import DjangoItem
import scrapy


class ProgramItem(DjangoItem):
    django_model = Program


class DancefloorEventItem(DjangoItem):
    django_model = DancefloorEvent
    date_string = scrapy.Field()
    timetable_updated = scrapy.Field()


class DancefloorEventDetailsItem(DjangoItem):
    django_model = DancefloorEventDetails
    date_string = scrapy.Field()
    time_string = scrapy.Field()
    rooms = scrapy.Field()
    is_completed = scrapy.Field()
    has_timetable = scrapy.Field()


class RoomItem(DjangoItem):
    django_model = Room
    slots = scrapy.Field()


class SlotItem(DjangoItem):
    django_model = Slot
    artists = scrapy.Field()
