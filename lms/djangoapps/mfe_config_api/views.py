"""
MFE API Views for useful information related to mfes.
"""

import json
import logging
import re

from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.views import APIView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from openedx.core.djangoapps.site_configuration.models import (
    SiteConfiguration
)

log = logging.getLogger(__name__)


class MFEConfigView(APIView):
    """
    Provides an API endpoint to get the MFE_CONFIG from site configuration.
    """

    @method_decorator(cache_page(settings.MFE_CONFIG_API_CACHE_TIMEOUT))
    def get(self, request):
        """
        GET /api/v1/mfe_config
        or
        GET /api/v1/mfe_config?mfe=name_of_mfe

        **GET Response Values**
        ```
        {
            "BASE_URL": "https://name_of_mfe.example.com",
            "LANGUAGE_PREFERENCE_COOKIE_NAME": "example-language-preference",
            "CREDENTIALS_BASE_URL": "https://credentials.example.com",
            "DISCOVERY_API_BASE_URL": "https://discovery.example.com",
            "LMS_BASE_URL": "https://courses.example.com",
            "LOGIN_URL": "https://courses.example.com/login",
            "LOGOUT_URL": "https://courses.example.com/logout",
            "STUDIO_BASE_URL": "https://studio.example.com",
            "LOGO_URL": "https://courses.example.com/logo.png"
        }
        ```
        """

        if not settings.ENABLE_MFE_CONFIG_API:
            return HttpResponseNotFound()

        # Remove the protocol and split the url at the slashes. Return the first entry for the domain name.
        mfe_config = {}

        log.info(
            "HTTP Referer %s", request.META.get('HTTP_REFERER')
        )
        log.info(
            "request.META %s", request.META
        )
        if request.META.get('HTTP_REFERER'):
            referer = re.sub('^https?:\/\/', '', request.META.get('HTTP_REFERER')).split('/')[0]  # nopep8

            for site_config in SiteConfiguration.objects.all():
                mfe_config = site_config.site_values.get("MFE_CONFIG", {})
                if mfe_config.get("BASE_URL"):
                    mfe_config_base_url = re.sub('^https?:\/\/', '', mfe_config.get("BASE_URL")).split('/')[0]  # nopep8

                    if mfe_config_base_url == referer:
                        log.info(
                            "Found the site configuration that matches the MFE base domain."
                        )

                        configuration = getattr(site_config.site, "configuration", None)

                        mfe_config = configuration.get_value(
                            f'MFE_CONFIG', getattr(settings, f'MFE_CONFIG', {}))

                        if request.query_params.get('mfe'):
                            mfe = str(request.query_params.get('mfe')).upper()

                            mfe_config.update(configuration.get_value(
                                f'MFE_CONFIG_{mfe}', getattr(settings, f'MFE_CONFIG_{mfe}', {})))

                        # Exit out of the loop once you find first correct
                        # MFE_CONFIG in Site Configuration.
                        break
        else:
            mfe_config = configuration_helpers.get_value('MFE_CONFIG', getattr(settings, 'MFE_CONFIG', {}))

            if request.query_params.get('mfe'):
                mfe = str(request.query_params.get('mfe')).upper()
                mfe_config.update(configuration_helpers.get_value(
                    f'MFE_CONFIG_{mfe}', getattr(settings, f'MFE_CONFIG_{mfe}', {})))

        log.info(
            "mfe_config = %s", mfe_config
        )
        return JsonResponse(mfe_config, status=status.HTTP_200_OK)
