# Generated by Django 4.2.9 on 2024-03-29 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0029_alter_overallrecapdata_first_message_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmessage',
            name='message',
            field=models.CharField(default='', max_length=1024),
        ),
    ]
