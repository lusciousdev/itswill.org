# Generated by Django 4.2.9 on 2024-03-21 04:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itswill_org', '0004_rename_commentor_chatmessage_commenter'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Chatter',
            new_name='TwitchUser',
        ),
    ]
