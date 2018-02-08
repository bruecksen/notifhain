import dateparser
import logging

from notifhain.event.models import Room, Slot, Artist

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
        event_details.event.completed = event_details_item["completed"]
        event_details.event.save()
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