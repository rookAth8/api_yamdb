# Generated by Django 2.2.16 on 2022-08-13 22:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_auto_20220813_2235'),
    ]

    operations = [
        migrations.RenameField(
            model_name='review',
            old_name='title',
            new_name='title_id',
        ),
    ]
