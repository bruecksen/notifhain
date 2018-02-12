from django.contrib import admin

from .models import Program, DancefloorEvent, DancefloorEventDetails, \
    Room, Slot, Artist


class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'month', 'url', 'last_updated', 'completed')
admin.site.register(Program, ProgramAdmin)


class DancefloorEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_date', 'url', 'last_updated', 'is_completed', 'has_timetable', 'is_notification_send')
    list_filter = ('program',)

admin.site.register(DancefloorEvent, DancefloorEventAdmin)


class DancefloorEventDetailsAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_date', 'url', 'last_updated')
admin.site.register(DancefloorEventDetails, DancefloorEventDetailsAdmin)


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name',)
admin.site.register(Room, RoomAdmin)


class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', )
admin.site.register(Artist, ArtistAdmin)


class SlotAdmin(admin.ModelAdmin):
    list_display = ('get_room', 'order', 'name', 'get_artist', 'time', 'is_live_set', 'is_closing')
    list_filter = ('room', 'event_details')

    def get_room(self, obj):
        return obj.room
    get_room.short_description = 'Room'

    def get_artist(self, obj):
        return ", ".join([a.name for a in obj.artists.all()])
    get_artist.short_description = 'Artist'

admin.site.register(Slot, SlotAdmin)
