# Generated by Django 5.1.1 on 2024-12-20 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0065_chatmessage_itswill_org_created_ed3b8e_idx'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='clip',
            index=models.Index(fields=['created_at'], name='itswill_org_created_ffe08a_idx'),
        ),
        migrations.AddIndex(
            model_name='clip',
            index=models.Index(fields=['view_count'], name='itswill_org_view_co_e960ce_idx'),
        ),
        migrations.AddIndex(
            model_name='twitchuser',
            index=models.Index(fields=['login'], name='itswill_org_login_91108a_idx'),
        ),
        migrations.AddIndex(
            model_name='twitchuser',
            index=models.Index(fields=['created_at'], name='itswill_org_created_2c343b_idx'),
        ),
        migrations.AddIndex(
            model_name='video',
            index=models.Index(fields=['created_at'], name='itswill_org_created_3d50ec_idx'),
        ),
        migrations.AddIndex(
            model_name='video',
            index=models.Index(fields=['view_count'], name='itswill_org_view_co_4cd414_idx'),
        ),
    ]
