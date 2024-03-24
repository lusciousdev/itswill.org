# Generated by Django 4.2.9 on 2024-03-23 05:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0011_monthlyrecap_total_chatters'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('vod_id', models.CharField(editable=False, max_length=255, primary_key=True, serialize=False)),
                ('stream_id', models.CharField(default='', max_length=255)),
                ('user_id', models.CharField(default='', max_length=255)),
                ('user_login', models.CharField(default='', max_length=255)),
                ('user_name', models.CharField(default='', max_length=255)),
                ('title', models.CharField(default='', max_length=255)),
                ('description', models.CharField(default='', max_length=512)),
                ('created_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='created at')),
                ('published_at', models.DateTimeField(default=datetime.datetime.now, verbose_name='published at')),
                ('url', models.CharField(default='', max_length=512)),
                ('thumbnail_url', models.CharField(default='', max_length=255)),
                ('viewable', models.CharField(default='', max_length=255)),
                ('view_count', models.IntegerField(default=0)),
                ('language', models.CharField(default='', max_length=255)),
                ('vod_type', models.CharField(default='', max_length=255)),
                ('duration', models.CharField(default='', max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='monthlyrecap',
            name='total_videos',
            field=models.IntegerField(default=0),
        ),
    ]
