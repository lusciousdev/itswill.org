# Generated by Django 4.2.9 on 2024-03-19 02:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatmessage',
            name='id',
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='message_id',
            field=models.CharField(editable=False, max_length=64, primary_key=True, serialize=False),
        ),
    ]
