# Generated by Django 4.2.9 on 2024-03-23 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0009_monthlyrecap_monthlyuserdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlyrecap',
            name='total_clip_views',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='monthlyrecap',
            name='total_clips',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='monthlyrecap',
            name='total_messages',
            field=models.IntegerField(default=0),
        ),
    ]
