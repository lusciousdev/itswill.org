# Generated by Django 5.2.4 on 2025-07-23 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0086_chatmessage_itswill_org_comment_f1f5f3_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fragment',
            name='case_sensitive',
            field=models.BooleanField(default=False),
        ),
    ]
