"""
Utility functions used by the bigcommerce_app.
"""

from django.conf import settings
from django.http import HttpResponse

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

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
    return configuration_helpers.get_value('BIGCOMMERCE_APP_CLIENT_ID', settings.BIGCOMMERCE_APP_CLIENT_ID)


def client_secret():
    return configuration_helpers.get_value('BIGCOMMERCE_APP_CLIENT_SECRET', settings.BIGCOMMERCE_APP_CLIENT_SECRET)


def platform_lms_url():
    return configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
