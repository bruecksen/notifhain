import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from notifhain.event.models import DancefloorEvent

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DancefloorEvent)
def send_timetable_email(sender, instance, created, **kwargs):
    logger.info("send_timetable_email")
    if instance.completed and not instance.notification_send:
        msg_plain = render_to_string('event-timetable-online.html', {'event': instance})
        send_emails_to = get_user_model().objects.all().values_list('email', flat=True)
        send_mail(
            'Timetable online: %s' % instance.name,
            msg_plain,
            settings.DEFAULT_FROM_EMAIL,
            send_emails_to,
            fail_silently=False,
        )
        instance.notification_send = True
        instance.save()
