# Generated by Django 5.1.1 on 2024-12-19 05:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0062_remove_overallrecapdata_count_clip_duration_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='overallwrappeddata',
            old_name='clip_duration',
            new_name='clip_watch_time',
        ),
        migrations.RenameField(
            model_name='userwrappeddata',
            old_name='clip_duration',
            new_name='clip_watch_time',
        ),
    ]
