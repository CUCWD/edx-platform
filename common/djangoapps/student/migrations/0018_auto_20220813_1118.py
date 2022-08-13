# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2022-08-13 15:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0017_auto_20220813_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[(b'm', b'Male'), (b'f', b'Female'), (b'nbtg', b'Non-binary / third gender'), (b'prefer-not-to-say', b'Prefer not to say')], db_index=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='level_of_education',
            field=models.CharField(blank=True, choices=[(b'some-hs', b'Some high school'), (b'hs', b'High School or GED'), (b'some-college', b'Some college'), (b'a', b'2-year degree'), (b'b', b'4-year degree'), (b'm', b"Master's"), (b'p', b'Doctorate'), (b'jd-md', b'Professional degree (J.D., M.D.)'), (b'prefer-not-to-say', b'Prefer not to say')], db_index=True, max_length=25, null=True),
        ),
    ]
