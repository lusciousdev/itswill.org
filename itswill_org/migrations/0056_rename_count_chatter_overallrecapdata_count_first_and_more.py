# Generated by Django 5.1.1 on 2024-12-17 03:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0055_overallrecapdata_count_chatter_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='overallrecapdata',
            old_name='count_chatter',
            new_name='count_first',
        ),
        migrations.RenameField(
            model_name='userrecapdata',
            old_name='count_chatter',
            new_name='count_first',
        ),
    ]
