# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('badges', '0004_auto_20190404_1154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeclass',
            name='slug',
            field=models.SlugField(unique=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='badgeclass',
            unique_together=set([('mode', 'course_id')]),
        ),
    ]
