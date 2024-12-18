# Generated by Django 5.1.1 on 2024-12-17 03:04

import itswill_org.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0056_rename_count_chatter_overallrecapdata_count_first_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_at_bot',
            field=itswill_org.models.StringCountField(default=0, verbose_name='Replies to itswillChat:'),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_at_bot',
            field=itswill_org.models.StringCountField(default=0, verbose_name='Replies to itswillChat:'),
        ),
    ]
