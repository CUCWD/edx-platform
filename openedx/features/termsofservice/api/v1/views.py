
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings

from openedx.features.termsofservice.models import TermsOfServiceSites, TermsOfService, TermsOfServiceAcknowledgement, TermsOfServiceAllSites
from django.contrib.sites.models import Site


@csrf_exempt
def terms_of_service_api(request):
    latest_tos_html = ''

    site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)

    if request.method == 'GET':
        """
            Return TOS as JSON
        """

        try:
            latest_tos_html = ''
            
            # Get the curf_id associated with the Site

            if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
                cur_site_id = Site.objects.get(domain = site_name)
                cur_site_curf_id = TermsOfServiceSites.objects.get(site_id = cur_site_id.id).curf_id
            else:
                cur_site_curf_id = TermsOfServiceAllSites.objects.all().first().curf_id

            current_valid_TOS = TermsOfService.objects.get(curf_id = cur_site_curf_id)
            
            cur_user_tos_ack = None
            cur_user_curf_id = None
            try:
                cur_user_tos_ack = TermsOfServiceAcknowledgement.objects.get(user_id = request.user.id, curf_id = cur_site_curf_id)
                if cur_user_tos_ack is not None:
                    cur_user_curf_id = cur_user_tos_ack.curf_id
            except TermsOfServiceAcknowledgement.DoesNotExist:
                cur_user_curf_id = None
                        
            has_user_agreed_to_latest_tos = False

            if settings.FEATURES.get('ENABLE_TERMSOFSERVICE_PER_SUBSITE'):
                # Check if the user agreed curf id matches the 
                has_user_agreed_to_latest_tos = cur_site_curf_id == cur_user_curf_id
            else:
                # check if user's agreed curf id is present in the TOS Site table
                # if the object is present, that implies that the user has agreed to the latest TOS

                try:
                    TermsOfServiceSites_curf_id = TermsOfServiceSites.objects.get(curf_id = cur_user_curf_id)
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
            "tos_html": latest_tos_html,
            "has_user_agreed_to_latest_tos": has_user_agreed_to_latest_tos
        }
        return JsonResponse(result)

    if request.method == 'POST':
        
        # Get the curf_id associated with the Site
        cur_site_id = Site.objects.get(domain = site_name)
        
        current_valid_curf_id = TermsOfServiceSites.objects.get(site_id = cur_site_id.id).curf_id
        try:
            user_TOS_ack = TermsOfServiceAcknowledgement.objects.get(user_id = request.user.id)
            user_TOS_ack.curf_id = current_valid_curf_id
        except TermsOfServiceAcknowledgement.DoesNotExist:
            user_TOS_ack = TermsOfServiceAcknowledgement(user_id = request.user.id, curf_id = current_valid_curf_id)
        user_TOS_ack.save()

        return HttpResponseRedirect(request.path_info)