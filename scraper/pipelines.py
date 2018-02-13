import dateparser
import logging
import datetime

from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from notifhain.event.models import Room, Slot, Artist, DancefloorEvent

logger = logging.getLogger('scrapy')


class DjangoPipeline(object):

    def item_to_model(self, item):
        model_class = getattr(item, 'django_model')
        if not model_class:
            raise TypeError("Item is not a `DjangoItem` or is misconfigured")

        return item.instance

    def get_or_create(self, model):
        model_class = type(model)
        created = False

        # Normally, we would use `get_or_create`. However, `get_or_create` would
        # match all properties of an object (i.e. create a new object
        # anytime it changed) rather than update an existing object.
        #
        # Instead, we do the two steps separately
        try:
            # We have no unique identifier at the moment; use the url for now.
            obj = model_class.objects.get(url=model.url)
        except model_class.DoesNotExist:
            created = True
            obj = model  # DjangoItem created a model for us.

        return (obj, created)

    def update_model(self, django_model, item, commit=True):
        pk = django_model.pk

        # item_dict = model_to_dict(item)
        item_dict = item.__dict__
        for (key, value) in item_dict.items():
            setattr(django_model, key, value)

        setattr(django_model, 'pk', pk)

        if commit:
            django_model.save()

        return django_model

    class Meta:
        abstract = True


class ProgramPipeline(DjangoPipeline):
    def process_item(self, item, spider):
        try:
            item_model = self.item_to_model(item)
            item_model.month = dateparser.parse(item["name"], "%Y-%m")
        except TypeError:
            return item

        model, created = self.get_or_create(item_model)
        self.update_model(model, item_model)
        logger.info("Program %s %s" % (item_model.name, created and 'created' or 'updated'))

        return item


class EventPipeline(DjangoPipeline):
    def process_item(self, item, spider):
        try:
            item_model = self.item_to_model(item)
            item_model.event_date = dateparser.parse(item["date_string"])
        except TypeError:
            return item

        model, created = self.get_or_create(item_model)
        # reset all state values
        # TODO should be handled differentyl, maybe a separte state model would be good
        item_model.is_completed = model.is_completed
        item_model.has_timetable = model.has_timetable
        item_model.is_notification_send = model.is_notification_send
        item.is_posted_to_rr = model.is_posted_to_rr
        item.timetable_updated = model.timetable_updated
        self.update_model(model, item_model)
        logger.info("Event %s %s" % (item_model.name, created and 'created' or 'updated'))

        return item


class EventDetailsPipeline(DjangoPipeline):
    def process_item(self, event_details_item, spider):
        try:
            item_model = self.item_to_model(event_details_item)
            item_model.event_date = dateparser.parse(
                "%s %s" % (event_details_item["date_string"],
                event_details_item["time_string"]),
                settings={'RETURN_AS_TIMEZONE_AWARE': True}
            )
        except TypeError:
            return event_details_item

        event_details, created = self.get_or_create(item_model)
        self.update_model(event_details, item_model)
        logger.info("EventDetail %s %s" % (item_model.name, created and 'created' or 'updated'))

        # delete all existing objects
        Slot.objects.filter(event_details=event_details).delete()
        for room_item in event_details_item["rooms"]:
            room, created = Room.objects.get_or_create(name=room_item["name"])
            for slot_item in room_item["slots"]:
                self.process_slot(slot_item, room, event_details, spider)
        event = event_details.event
        event.is_completed = event_details_item["is_completed"]
        if event.is_completed and not event.timetable_updated:
            event.timetable_updated = datetime.datetime.now()
        if not event.is_completed and datetime.datetime.now().date() > event.event_date:
            event.is_completed = True
        event.save()

        return event_details_item

    def process_slot(self, slot_item, room, event_details, spider):
        try:
            item_model = self.item_to_model(slot_item)
        except TypeError:
            return slot_item
        item_model.room = room
        item_model.event_details = event_details
        # add artists to slot
        item_model.save()
        for artist in slot_item["artists"]:
            artist, created = Artist.objects.get_or_create(name=artist)
            item_model.artists.add(artist)
        return slot_item

    def close_spider(self, spider):
        today = datetime.date.today()
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        events = DancefloorEvent.objects.filter(has_timetable=True, is_notification_send=False, event_details__event_date__lte=next_monday)
        for event in events:
            logger.info("send_timetable_email: " + event)
            msg_plain = render_to_string('event-timetable-online.html', {'event': event})
            send_emails_to = get_user_model().objects.all().values_list('email', flat=True)
            send_mail(
                'Timetable online: %s %s' % (event.name, event.event_date),
                msg_plain,
                settings.DEFAULT_FROM_EMAIL,
                send_emails_to,
                fail_silently=False,
            )
            event.is_notification_send = True
            event.save()
