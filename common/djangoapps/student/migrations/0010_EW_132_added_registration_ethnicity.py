# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_EW_132_added_registration_zipcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='ethnicity',
            field=models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'w', b'White'), (b'hl', b'Hispanic or Latino'), (b'ba', b'Black or African American'), (b'na', b'Native American or American Indian'), (b'api', b'Asian / Pacific Islander'), (b'other', b'Other ethnicity')]),
        ),
    ]
