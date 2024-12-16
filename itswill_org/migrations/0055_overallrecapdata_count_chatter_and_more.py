# Generated by Django 5.1.1 on 2024-12-16 05:24

import itswill_org.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0054_overallrecapdata_count_clip_duration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_chatter',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_what',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_chatter',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_what',
            field=itswill_org.models.StringCountField(default=0),
        ),
    ]
