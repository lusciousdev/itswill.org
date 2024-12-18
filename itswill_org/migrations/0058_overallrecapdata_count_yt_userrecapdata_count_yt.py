# Generated by Django 5.1.1 on 2024-12-18 01:45

import itswill_org.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0057_overallrecapdata_count_at_bot_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_yt',
            field=itswill_org.models.StringCountField(default=0, verbose_name='YouTube links:'),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_yt',
            field=itswill_org.models.StringCountField(default=0, verbose_name='YouTube links:'),
        ),
    ]