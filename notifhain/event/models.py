import datetime

from django.db import models


class ProgramManager(models.Manager):
    def completed(self, **kwargs):
        return self.filter(is_completed=True)

    def uncompleted(self, **kwargs):
        return self.filter(is_completed=False)


class EventQuerySet(models.QuerySet):
    def completed(self, **kwargs):
        return self.filter(is_completed=True)

    def uncompleted(self, **kwargs):
        return self.filter(is_completed=False)

    def new(self, **kwargs):
        return self.filter(is_completed=None)

    def till_sunday(self, **kwargs):
        today = datetime.date.today()
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        return self.filter(event_details__event_date__lt=next_monday)

    def get_next_klubnacht(self, **kwargs):
        return self.filter(name__icontains="klubnacht", event_details__event_date__gte=datetime.datetime.now()).first()


class Program(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    month = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    objects = ProgramManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Programs"
        ordering = ["month", ]


class DancefloorEvent(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    event_date = models.DateField(blank=True, null=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)
    is_completed = models.NullBooleanField(default=None, null=True, blank=True)
    has_timetable = models.BooleanField(default=False)
    is_notification_send = models.BooleanField(default=False)
    is_posted_to_rr = models.BooleanField(default=False)
    timetable_updated = models.DateTimeField(blank=True, null=True)

    objects = EventQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["event_date", ]

    def mark_as_completed(self):
        self.completed = True
        self.save()

    def get_rooms(self):
        return Room.objects.distinct().filter(slots__event_details__event=self)

    def get_slots(self, room):
        return self.event_details.slots.filter(room=room)


class DancefloorEventDetails(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)
    event = models.OneToOneField(DancefloorEvent, on_delete=models.CASCADE, related_name='event_details')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s %s" % (self.name, self.event_date)

    class Meta:
        verbose_name = "Event Detail"
        verbose_name_plural = "Event Details"
        ordering = ["event_date"]


class Room(models.Model):
    name = models.CharField(max_length=500)
    order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Slot(models.Model):
    event_details = models.ForeignKey(DancefloorEventDetails, on_delete=models.CASCADE, related_name='slots')
    name = models.CharField(max_length=500)
    artists = models.ManyToManyField(Artist)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='slots')
    time = models.CharField(max_length=500, blank=True, null=True)
    order = models.SmallIntegerField()
    is_live_set = models.BooleanField(default=False)
    is_closing = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Slots"
        ordering = ["room", "order"]
