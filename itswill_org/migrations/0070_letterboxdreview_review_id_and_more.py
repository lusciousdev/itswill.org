# Generated by Django 5.1.1 on 2025-04-08 05:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0069_letterboxdreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='letterboxdreview',
            name='review_id',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='letterboxdreview',
            name='movie_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterUniqueTogether(
            name='letterboxdreview',
            unique_together={('review_id',)},
        ),
    ]
