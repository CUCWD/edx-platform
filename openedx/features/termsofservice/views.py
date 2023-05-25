from .models import TermsOfService, TermsOfServiceAllSites, TermsOfServiceSites
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

import json

def latest_terms_of_service():
    # latest_tos = TermsOfService.objects.latest('date_modified')
    # context = {'tos_html': latest_tos.terms_of_service_text}
    # return render_to_string( 'termsofservice/tos_content.html', context)
    site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
    if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
        cur_site_id = Site.objects.get(domain = site_name)
        cur_site_curf_id = TermsOfServiceSites.objects.get(site_id = cur_site_id.id).curf_id
    else:
        cur_site_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id

    tos_html = TermsOfService.objects.get(curf_id = cur_site_curf_id).terms_of_service_text

    context = {'tos_html': tos_html}
    return render_to_string( 'termsofservice/tos_content.html', context)
