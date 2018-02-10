# Generated by Django 2.0.1 on 2018-02-10 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0009_auto_20180208_1452'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dancefloorevent',
            options={'ordering': ['event_date'], 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AlterModelOptions(
            name='danceflooreventdetails',
            options={'ordering': ['event_date'], 'verbose_name': 'Event Detail', 'verbose_name_plural': 'Event Details'},
        ),
        migrations.AddField(
            model_name='dancefloorevent',
            name='timetable_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]