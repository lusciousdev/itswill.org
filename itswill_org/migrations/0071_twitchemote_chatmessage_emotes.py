# Generated by Django 5.1.1 on 2025-06-24 00:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0070_letterboxdreview_review_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwitchEmote',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('emote_id', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='emotes',
            field=models.ManyToManyField(to='itswill_org.twitchemote'),
        ),
    ]
