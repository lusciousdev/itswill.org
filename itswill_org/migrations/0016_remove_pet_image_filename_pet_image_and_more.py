# Generated by Django 4.2.9 on 2024-03-23 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0015_pet_kill_term_pluralize_alter_pet_kill_term'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pet',
            name='image_filename',
        ),
        migrations.AddField(
            model_name='pet',
            name='image',
            field=models.FileField(default=None, upload_to='petimg/'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pet',
            name='kill_term_pluralize',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
