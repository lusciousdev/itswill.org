# Generated by Django 5.1.1 on 2024-12-20 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0064_alter_overallrecapdata_count_clip_watch_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['created_at'], name='itswill_org_created_ed3b8e_idx'),
        ),
    ]
