# lint-amnesty, pylint: disable=missing-module-docstring

import json
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseRedirect, JsonResponse
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings

from openedx.features.termsofservice.models import TermsOfServiceSites, TermsOfService
from openedx.features.termsofservice.models import TermsOfServiceAcknowledgement, TermsOfServiceAllSites
from django.contrib.sites.models import Site


@ensure_csrf_cookie
def terms_of_service_api(request):  # lint-amnesty, pylint: disable=missing-function-docstring
    latest_tos_html = ''

    cur_site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
    cur_site_id = Site.objects.get(domain = cur_site_name)

    if request.method == 'GET':
        # Return Terms of Service as JSON
        try:
            latest_tos_html = ''
            has_user_agreed_to_latest_tos = False
            # Get the curf_id associated with the Site
            if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
                cur_site_curf_id = TermsOfServiceSites.objects.get(site_id = cur_site_id.id).curf_id
            else:
                default_tos = TermsOfServiceAllSites.objects.all().first()
                #if there is no default TOS assigned, return a JSON response with an error
                if default_tos is None:
                    result = {
                        "tos_html": latest_tos_html,
                        "tos_exists_for_site": False,
                        "has_user_agreed_to_latest_tos": has_user_agreed_to_latest_tos,
                        "error": f"Need to setup a Terms of Service Acknowledgment for {cur_site_name}"
                    }
                    return JsonResponse(result)
                else:
                    cur_site_curf_id = default_tos.curf_id

            current_valid_TOS = TermsOfService.objects.get(curf_id=cur_site_curf_id)

            cur_user_tos_ack = None
            cur_user_curf_id = None
            try:
                cur_user_tos_ack = TermsOfServiceAcknowledgement.objects.get(
                    user_id=request.user.id, curf_id=cur_site_curf_id)
                if cur_user_tos_ack is not None:
                    cur_user_curf_id = cur_user_tos_ack.curf_id
            except TermsOfServiceAcknowledgement.DoesNotExist:
                cur_user_curf_id = None

            if not settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
                # Check if the user agreed curf id matches the latest curf id
                has_user_agreed_to_latest_tos = cur_site_curf_id == cur_user_curf_id
            else:
                # check if user's agreed curf id is present in the TOS Site table
                # if the object is present, that implies that the user has agreed to the latest TOS

                try:
                    TermsOfServiceSites_curf_id = TermsOfServiceSites.objects.get(curf_id=cur_user_curf_id)
                    if TermsOfServiceSites_curf_id is not None:
                        has_user_agreed_to_latest_tos = True
                except TermsOfServiceSites.DoesNotExist:
                    has_user_agreed_to_latest_tos = False

            if not has_user_agreed_to_latest_tos:
                # get the html text using the curf id
                latest_tos_html = current_valid_TOS.terms_of_service_text
        except TermsOfServiceAcknowledgement.DoesNotExist:
            latest_tos_html = ''

        result = {
            "tos_exists_for_site": True if latest_tos_html else False,
            "tos_html": latest_tos_html,
            "has_user_agreed_to_latest_tos": has_user_agreed_to_latest_tos
        }

        return JsonResponse(result)

    if request.method == 'POST':
        
        if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
            current_valid_curf_id = TermsOfServiceSites.objects.get(site_id = cur_site_id.id).curf_id
        else:
            current_valid_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id

        try:
            user_TOS_ack = TermsOfServiceAcknowledgement.objects.get(user_id=request.user.id)
            user_TOS_ack.curf_id = current_valid_curf_id
        except TermsOfServiceAcknowledgement.DoesNotExist:
            user_TOS_ack = TermsOfServiceAcknowledgement(user_id=request.user.id, curf_id=current_valid_curf_id)
        user_TOS_ack.save()

        return HttpResponseRedirect(request.path_info)
