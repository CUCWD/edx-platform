# Generated by Django 2.2.20 on 2021-04-27 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0041_registration_activation_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='allow_certificate',
            field=models.BooleanField(default=1, null=True),
        ),
    ]
