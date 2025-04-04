# Generated by Django 4.2.11 on 2024-08-23 03:00

from django.db import migrations
import itswill_org.models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0037_alter_clip_options_alter_pet_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_chicken',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_cum',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_dance',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_dankies',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_etsmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_gasp',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_giggle',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_ksmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_love',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_lul',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_mmylc',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_monka',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_pog',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_pogo',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_pound',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_seven',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_shoop',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_sit',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_sneak',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_sonic',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_spin',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_stsmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='overallrecapdata',
            name='count_vvkool',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_chicken',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_cum',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_dance',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_dankies',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_etsmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_gasp',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_giggle',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_ksmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_love',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_lul',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_mmylc',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_monka',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_pog',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_pogo',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_pound',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_seven',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_shoop',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_sit',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_sneak',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_sonic',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_spin',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_stsmg',
            field=itswill_org.models.StringCountField(default=0),
        ),
        migrations.AlterField(
            model_name='userrecapdata',
            name='count_vvkool',
            field=itswill_org.models.StringCountField(default=0),
        ),
    ]
