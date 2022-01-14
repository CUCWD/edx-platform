# Generated by Django 3.2.10 on 2022-01-14 20:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0003_historicalorganizationcourse'),
        ('third_party_auth', '0005_auto_20210723_1527'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailProviderConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('icon_class', models.CharField(blank=True, default='fa-sign-in', help_text='The Font Awesome (or custom) icon class to use on the login button for this provider. Examples: fa-google-plus, fa-facebook, fa-linkedin, fa-sign-in, fa-university', max_length=50)),
                ('icon_image', models.FileField(blank=True, help_text='If there is no Font Awesome icon available for this provider, upload a custom image. SVG images are recommended as they can scale to any size.', upload_to='')),
                ('name', models.CharField(help_text='Name of this provider (shown to users)', max_length=50)),
                ('slug', models.SlugField(default='default', help_text='A short string uniquely identifying this provider. Cannot contain spaces and should be a usable as a CSS class. Examples: "ubc", "mit-staging"', max_length=30)),
                ('secondary', models.BooleanField(default=False, help_text='Secondary providers are displayed less prominently, in a separate list of "Institution" login providers.')),
                ('skip_hinted_login_dialog', models.BooleanField(default=False, help_text='If this option is enabled, users that visit a "TPA hinted" URL for this provider (e.g. a URL ending with `?tpa_hint=[provider_name]`) will be forwarded directly to the login URL of the provider instead of being first prompted with a login dialog.')),
                ('skip_registration_form', models.BooleanField(default=False, help_text='If this option is enabled, users will not be asked to confirm their details (name, email, etc.) during the registration process. Only select this option for trusted providers that are known to provide accurate user information.')),
                ('skip_email_verification', models.BooleanField(default=False, help_text='If this option is selected, users will not be required to confirm their email, and their account will be activated immediately upon registration.')),
                ('send_welcome_email', models.BooleanField(default=False, help_text='If this option is selected, users will be sent a welcome email upon registration.')),
                ('visible', models.BooleanField(default=False, help_text='If this option is not selected, users will not be presented with the provider as an option to authenticate with on the login screen, but manual authentication using the correct link is still possible.')),
                ('max_session_length', models.PositiveIntegerField(blank=True, default=None, help_text='If this option is set, then users logging in using this SSO provider will have their session length limited to no longer than this value. If set to 0 (zero), the session will expire upon the user closing their browser. If left blank, the Django platform session default length will be used.', null=True, verbose_name='Max session length (seconds)')),
                ('send_to_registration_first', models.BooleanField(default=False, help_text='If this option is selected, users will be directed to the registration page immediately after authenticating with the third party instead of the login page.')),
                ('sync_learner_profile_data', models.BooleanField(default=False, help_text='Synchronize user profile data received from the identity provider with the edX user account on each SSO login. The user will be notified if the email address associated with their account is changed as a part of this synchronization.')),
                ('enable_sso_id_verification', models.BooleanField(default=False, help_text='Use the presence of a profile from a trusted third party as proof of identity verification.')),
                ('disable_for_enterprise_sso', models.BooleanField(default=False, help_text='IDPs with this set to True will be excluded from the dropdown IDP selection in the EnterpriseCustomer Django Admin form.', verbose_name='Disabled for Enterprise TPA')),
                ('backend_name', models.CharField(db_index=True, help_text='Which python-social-auth Email provider backend to use. The list of backend choices is determined by the THIRD_PARTY_AUTH_BACKENDS setting.', max_length=50)),
                ('other_settings', models.TextField(blank=True, help_text='Optional JSON object with advanced settings, if any.')),
                ('changed_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Changed by')),
                ('organization', models.ForeignKey(blank=True, help_text='optional. If this provider is an Organization, this attribute can be used reference users in that Organization', null=True, on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('site', models.ForeignKey(default=1, help_text='The Site that this provider configuration belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='emailproviderconfigs', to='sites.site')),
            ],
            options={
                'verbose_name': 'Provider Configuration (Email)',
                'verbose_name_plural': 'Provider Configuration (Email)',
            },
        ),
    ]
