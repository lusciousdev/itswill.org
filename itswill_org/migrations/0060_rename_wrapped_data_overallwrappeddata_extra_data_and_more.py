# Generated by Django 5.1.1 on 2024-12-18 06:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0059_overallrecapdata_count_q_userrecapdata_count_q'),
    ]

    operations = [
        migrations.RenameField(
            model_name='overallwrappeddata',
            old_name='wrapped_data',
            new_name='extra_data',
        ),
        migrations.RenameField(
            model_name='userwrappeddata',
            old_name='wrapped_data',
            new_name='extra_data',
        ),
        migrations.AddField(
            model_name='overallwrappeddata',
            name='clip_duration',
            field=models.CharField(default='0 seconds', max_length=255),
        ),
        migrations.AddField(
            model_name='overallwrappeddata',
            name='jackass_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='overallwrappeddata',
            name='recap',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='itswill_org.overallrecapdata'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='overallwrappeddata',
            name='typing_time',
            field=models.CharField(default='0 seconds', max_length=255),
        ),
        migrations.AddField(
            model_name='userwrappeddata',
            name='clip_duration',
            field=models.CharField(default='0 seconds', max_length=255),
        ),
        migrations.AddField(
            model_name='userwrappeddata',
            name='jackass_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userwrappeddata',
            name='recap',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='itswill_org.userrecapdata'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userwrappeddata',
            name='typing_time',
            field=models.CharField(default='0 seconds', max_length=255),
        ),
    ]