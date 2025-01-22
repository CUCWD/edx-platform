from django.conf import settings
from django.contrib.sites.models import Site
from django.db import migrations

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class Migration(migrations.Migration):

    dependencies = [
        ('termsofservice', '0001_initial'),
    ]

    def forwards(apps, schema_editor):

        TermsOfService = apps.get_model('termsofservice', 'TermsOfService')
        # create a sample terms of service object
        tos = TermsOfService(date_modified='2023-01-01 00:00:00', terms_of_service_text='<p>Sample terms of service</p>', curf_id='test-2023-01')
        tos.save()

        # get the previously created terms of service object
        tos = apps.get_model('termsofservice', 'TermsOfService').objects.get(curf_id='test-2023-01')

        if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
            site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
            Site = apps.get_model('sites', 'Site')
            cur_site = Site.objects.get(domain=site_name)

            TermsOfServiceSites = apps.get_model('termsofservice', 'TermsOfServiceSites')
            tos_sites = TermsOfServiceSites.objects.create(site_id=cur_site.id, curf=tos)
            tos_sites.save()
        else:
            TermsOfServiceAllSites = apps.get_model('termsofservice', 'TermsOfServiceAllSites')

            # create a sample terms of service all sites object
            tos_all_sites = TermsOfServiceAllSites(curf=tos)
            tos_all_sites.save()

    def backwards(apps, schema_editor):
        TermsOfService = apps.get_model('termsofservice', 'TermsOfService')
        tos = TermsOfService.objects.get(curf_id='test-2023-01')

        if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
            site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
            Site = apps.get_model('sites', 'Site')
            cur_site = Site.objects.get(domain=site_name)

            TermsOfServiceSites = apps.get_model('termsofservice', 'TermsOfServiceSites')
            try:
                tos_sites = TermsOfServiceSites.objects.get(site=cur_site.id, curf=tos)
                tos_sites.delete()
                tos.delete()
            except (TermsOfServiceSites.DoesNotExist, TermsOfService.DoesNotExist) as error:
                print(f"Error: {error}")
        else:
            TermsOfServiceAllSites = apps.get_model('termsofservice', 'TermsOfServiceAllSites')
            try:
                tos_all_sites = TermsOfServiceAllSites.objects.get(curf=tos)
                tos_all_sites.delete()
                tos.delete()
            except (TermsOfServiceAllSites.DoesNotExist, TermsOfService.DoesNotExist) as error:
                print(f"Error: {error}")

    operations = [
        migrations.RunPython(forwards, backwards),
    ]