# lint-amnesty, pylint: disable=missing-module-docstring

from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings
from django.shortcuts import redirect

from openedx.features.termsofservice.models import TermsOfServiceSites, TermsOfService
from openedx.features.termsofservice.models import TermsOfServiceAcknowledgement, TermsOfServiceAllSites
from django.contrib.sites.models import Site


@ensure_csrf_cookie
def terms_of_service_api(request):  # lint-amnesty, pylint: disable=missing-function-docstring
    latest_tos_html = ''

    cur_site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)
    cur_site_id = Site.objects.get(domain=cur_site_name)

    if request.method == 'GET':
        # Return Terms of Service as JSON
        try:
            latest_tos_html = ''
            has_user_agreed_to_latest_tos = False

            if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
                # Get the curf_id associated with the Site
                cur_site_curf_id = TermsOfServiceSites.objects.get(site_id=cur_site_id.id).curf_id
                cur_user_tos_ack = TermsOfServiceAcknowledgement.objects.filter(
                    user_id=request.user.id, curf_id=cur_site_curf_id).first()

                # Check if the user agreed curf id matches the latest curf id

                if cur_user_tos_ack is not None and cur_site_curf_id == cur_user_tos_ack.curf_id:
                    has_user_agreed_to_latest_tos = True
                else:
                    latest_tos_html = TermsOfService.objects.get(curf_id=cur_site_curf_id).terms_of_service_text

            else:
                default_tos = TermsOfServiceAllSites.objects.all().first()

                #if there is no default TOS assigned, return a JSON response with an error
                if default_tos is None:
                    result = {
                        "tos_html": latest_tos_html,
                        "tos_exists_for_site": False,
                        "has_user_agreed_to_latest_tos": has_user_agreed_to_latest_tos,
                        "Error": f"Need to setup a Terms of Service Acknowledgment for {cur_site_name}"
                    }
                    return JsonResponse(result)

                cur_site_curf_id = default_tos.curf_id
                cur_user_tos_ack = TermsOfServiceAcknowledgement.objects.filter(
                    user_id=request.user.id, curf_id=cur_site_curf_id).first()

                # Check if user's agreed curf id is present in the TOS Site table
                # if the object is present, that implies that the user has agreed to the latest TOS
                if cur_user_tos_ack is not None and cur_site_curf_id == cur_user_tos_ack.curf_id:
                    has_user_agreed_to_latest_tos = True
                else:
                    latest_tos_html = TermsOfService.objects.get(curf_id=cur_site_curf_id).terms_of_service_text

        except TermsOfServiceAcknowledgement.DoesNotExist:
            latest_tos_html = ''

        result = {
            "tos_exists_for_site": bool(latest_tos_html),
            "tos_html": latest_tos_html,
            "has_user_agreed_to_latest_tos": has_user_agreed_to_latest_tos
        }

        return JsonResponse(result)

    if request.method == 'POST':

        if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
            current_valid_curf_id = TermsOfServiceSites.objects.get(site_id=cur_site_id.id).curf_id
        else:
            current_valid_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id

        if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
            current_valid_curf_id = TermsOfServiceSites.objects.get(site_id=cur_site_id.id).curf_id
        else:
            current_valid_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id

        try:
            user_TOS_ack = TermsOfServiceAcknowledgement.objects.get(user_id=request.user.id)
            user_TOS_ack.curf_id = current_valid_curf_id
        except TermsOfServiceAcknowledgement.DoesNotExist:
            user_TOS_ack = TermsOfServiceAcknowledgement(user_id=request.user.id, curf_id=current_valid_curf_id)
        user_TOS_ack.save()

        return redirect(request.path_info)
