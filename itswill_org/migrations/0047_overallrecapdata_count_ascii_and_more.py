# Generated by Django 5.1.1 on 2024-12-14 03:41

import itswill_org.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0046_overallrecapdata_count_caw_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_ascii',
            field=models.IntegerField(default=0, verbose_name='ASCIIs sent:'),
        ),
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_goose',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_kirb',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='overallrecapdata',
            name='count_monka2',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_ascii',
            field=models.IntegerField(default=0, verbose_name='ASCIIs sent:'),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_goose',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_kirb',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='count_monka2',
            field=itswill_org.models.StringCountField(default=0),
        ),
    ]