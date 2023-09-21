# Generated by Django 3.2.20 on 2023-09-04 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussions', '0017_alter_historicaldiscussionsconfiguration_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discussionsconfiguration',
            name='posting_restrictions',
            field=models.CharField(choices=[('enabled', 'Enabled'), ('disabled', 'Disabled'), ('scheduled', 'Scheduled')], default='disabled', help_text='The Posting availability in discussions whether it will be enabled, scheduled or indefinitely disabled.', max_length=15),
        ),
        migrations.AlterField(
            model_name='historicaldiscussionsconfiguration',
            name='posting_restrictions',
            field=models.CharField(choices=[('enabled', 'Enabled'), ('disabled', 'Disabled'), ('scheduled', 'Scheduled')], default='disabled', help_text='The Posting availability in discussions whether it will be enabled, scheduled or indefinitely disabled.', max_length=15),
        ),
    ]
