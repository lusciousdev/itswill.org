# Generated by Django 5.1.1 on 2024-12-14 05:10

import itswill_org.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0048_twitchuser_is_bot'),
    ]

    operations = [
        migrations.AddField(
            model_name='overallrecapdata',
            name='last_message',
            field=models.CharField(default='', max_length=1024, verbose_name='Last message:'),
        ),
        migrations.AddField(
            model_name='userrecapdata',
            name='last_message',
            field=models.CharField(default='', max_length=1024, verbose_name='Last message:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_ascii',
            field=itswill_org.models.StatField(default=0, verbose_name='ASCIIs sent:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_characters',
            field=itswill_org.models.BigStatField(default=0, verbose_name='Total characters:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_chatters',
            field=itswill_org.models.StatField(default=0, verbose_name='Number of chatters:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_clip_views',
            field=itswill_org.models.StatField(default=0, verbose_name='Views on those clips:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_clips',
            field=itswill_org.models.StatField(default=0, verbose_name='Clips created:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_messages',
            field=itswill_org.models.StatField(default=0, verbose_name='Messages sent:'),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_videos',
            field=itswill_org.models.StatField(default=0, verbose_name='Number of videos:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_ascii',
            field=itswill_org.models.StatField(default=0, verbose_name='ASCIIs sent:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_characters',
            field=itswill_org.models.BigStatField(default=0, verbose_name='Total characters:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_chatters',
            field=itswill_org.models.StatField(default=0, verbose_name='Number of chatters:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_clip_views',
            field=itswill_org.models.StatField(default=0, verbose_name='Views on those clips:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_clips',
            field=itswill_org.models.StatField(default=0, verbose_name='Clips created:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_messages',
            field=itswill_org.models.StatField(default=0, verbose_name='Messages sent:'),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_videos',
            field=itswill_org.models.StatField(default=0, verbose_name='Number of videos:'),
        ),
    ]
