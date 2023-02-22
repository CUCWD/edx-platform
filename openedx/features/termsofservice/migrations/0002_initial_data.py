from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('termsofservice', '0001_initial'),
    ]

    def forwards(apps, schema_editor):

        TermsOfService = apps.get_model('termsofservice', 'TermsOfService')
        # create a sample terms of service object
        tos = TermsOfService(date_modified='2023-01-01 00:00:00', terms_of_service_text='<p>Sample terms of service</p>', curf_id='test-2023-01')
        tos.save()

        TermsOfServiceAllSites = apps.get_model('termsofservice', 'TermsOfServiceAllSites')
        # get the previously created terms of service object
        tos = apps.get_model('termsofservice', 'TermsOfService').objects.get(curf_id='test-2023-01')
        # create a sample terms of service all sites object
        tos_all_sites = TermsOfServiceAllSites(curf=tos)
        tos_all_sites.save()

    def backwards(apps, schema_editor):
        TermsOfService = apps.get_model('termsofservice', 'TermsOfService')
        TermsOfServiceAllSites = apps.get_model('termsofservice', 'TermsOfServiceAllSites')
        try:
            tos = TermsOfService.objects.get(curf_id='test-2023-01')
            tos_all_sites = TermsOfServiceAllSites.objects.get(curf=tos)
            tos_all_sites.delete()
            tos.delete()
        except TermsOfService.DoesNotExist as error:
            print(f"Error: {error}")

    operations = [
        migrations.RunPython(forwards, backwards),
    ]