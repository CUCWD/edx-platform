# Generated by Django 3.2.13 on 2022-08-12 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0044_auto_20220808_2144'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female'), ('nbtg', 'Non-binary / third gender'), ('prefer-not-to-say', 'Prefer not to say')], db_index=True, max_length=25, null=True),
        ),
    ]
