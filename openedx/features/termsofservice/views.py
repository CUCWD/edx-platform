# lint-amnesty, pylint: disable=missing-module-docstring

from .models import TermsOfService, TermsOfServiceAllSites, TermsOfServiceSites
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import logging

logger = logging.getLogger(__name__)


def latest_terms_of_service():  # lint-amnesty, pylint: disable=missing-function-docstring
    site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
    msg = (
        f"Need to setup a Terms of Service Acknowledgment for {site_name}"
    )
    tos_html = msg
    cur_site_curf_id = None

    if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
        try:
            cur_site_id = Site.objects.get(domain=site_name)
            cur_site_curf_id = TermsOfServiceSites.objects.get(site_id=cur_site_id.id).curf_id
        except (TermsOfServiceSites.DoesNotExist, AttributeError) as error:
            logger.info(f"{msg}\n{str(error)}")
    else:
        try:
            cur_site_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id
        except (TermsOfServiceAllSites.DoesNotExist, AttributeError) as error:
            logger.info(f"{msg}\n{str(error)}")

    if cur_site_curf_id is not None:
        tos_html = TermsOfService.objects.get(curf_id=cur_site_curf_id).terms_of_service_text

    context = {'tos_html': tos_html}
    return render_to_string('termsofservice/tos_content.html', context)
