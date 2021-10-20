"""
Utility functions used by the bigcommerce_app.
"""

from django.conf import settings
from django.http import HttpResponse

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

def requires_bigcommerce_enabled(function):
    """
    Decorator that bails a function out early if bigcommerce isn't enabled.
    """
    def wrapped(*args, **kwargs):
        """
        Wrapped function which bails out early if bagdes aren't enabled.
        """
        if not bigcommerce_enabled():
            return
        return function(*args, **kwargs)
    return wrapped


def bigcommerce_enabled():
    """
    returns a boolean indicating whether or not BigCommerce app is enabled.
    """
    return configuration_helpers.get_value_for_org('ENABLE_BIGCOMMERCE', "SITE_NAME", settings.ENABLE_BIGCOMMERCE)

#
# Error handling and helpers
#
def _error_info(e):
    content = ""
    try:  # it's probably a HttpException, if you're using the bigcommerce client
        content += str(e.headers) + "<br>" + str(e.content) + "<br>"
        req = e.response.request
        content += "<br>Request:<br>" + req.url + "<br>" + str(req.headers) + "<br>" + str(req.body)
    except AttributeError as e:  # not a HttpException
        content += "<br><br> (This page threw an exception: {})".format(str(e))
    return content


def internal_server_error(e):
    content = "Internal Server Error: " + str(e) + "<br>"
    content += _error_info(e)
    return HttpResponse(content, status=500)


def client_id():
    return configuration_helpers.get_value_for_org('BIGCOMMERCE_APP_CLIENT_ID', "SITE_NAME", settings.BIGCOMMERCE_APP_CLIENT_ID)


def client_secret():
    return configuration_helpers.get_value_for_org('BIGCOMMERCE_APP_CLIENT_SECRET', "SITE_NAME", settings.BIGCOMMERCE_APP_CLIENT_SECRET)


def platform_lms_url():
    return configuration_helpers.get_value_for_org('LMS_ROOT_URL', "SITE_NAME", settings.LMS_ROOT_URL)
