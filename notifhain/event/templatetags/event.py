from django import template

register = template.Library()


@register.simple_tag
def get_room_slots(event, room):
    return event.get_slots(room)
