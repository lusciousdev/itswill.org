# Generated by Django 5.1.1 on 2024-12-14 04:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0047_overallrecapdata_count_ascii_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='twitchuser',
            name='is_bot',
            field=models.BooleanField(default=False),
        ),
    ]