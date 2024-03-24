# Generated by Django 4.2.9 on 2024-03-21 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0007_alter_clip_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(editable=False, max_length=255, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='clip',
            name='clip_id',
            field=models.CharField(editable=False, max_length=255, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='clip',
            name='embed_url',
            field=models.CharField(default='missing embed url', max_length=512),
        ),
        migrations.AlterField(
            model_name='clip',
            name='game_id',
            field=models.CharField(default='missing game id', max_length=255),
        ),
        migrations.AlterField(
            model_name='clip',
            name='language',
            field=models.CharField(default='en', max_length=255),
        ),
        migrations.AlterField(
            model_name='clip',
            name='thumbnail_url',
            field=models.CharField(default='missing thumbnail url', max_length=512),
        ),
        migrations.AlterField(
            model_name='clip',
            name='title',
            field=models.CharField(default='missing clip title', max_length=255),
        ),
        migrations.AlterField(
            model_name='clip',
            name='url',
            field=models.CharField(default='missing clip url', max_length=512),
        ),
        migrations.AlterField(
            model_name='clip',
            name='video_id',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='broadcaster_type',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='description',
            field=models.CharField(default='', max_length=512),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='display_name',
            field=models.CharField(default='missing display name', max_length=255),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='login',
            field=models.CharField(default='missing username', max_length=255),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='offline_image_url',
            field=models.CharField(default='missing offline image url', max_length=512),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='profile_image_url',
            field=models.CharField(default='missing profile image url', max_length=512),
        ),
        migrations.AlterField(
            model_name='twitchuser',
            name='user_type',
            field=models.CharField(default='', max_length=255),
        ),
    ]
