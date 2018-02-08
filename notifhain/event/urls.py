from django.urls import path

from notifhain.event.views import EventTimetableView

urlpatterns = [
    path('timetable/<int:pk>/', EventTimetableView.as_view())
]
