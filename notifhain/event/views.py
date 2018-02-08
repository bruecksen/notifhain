from django.views.generic import DetailView

from notifhain.event.models import DancefloorEvent


class EventTimetableView(DetailView):
    template_name = "event-timetable-online.html"
    model = DancefloorEvent
    context_object_name = 'event'
