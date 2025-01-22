# pylint: disable=missing-module-docstring

"""
Contains URLs for the Terms of Service API
"""
from django.urls import path
from django.contrib.auth.decorators import login_required

from openedx.features.termsofservice.api.v1.views import terms_of_service_api

urlpatterns = [
    path('v1/current_tos/', login_required(terms_of_service_api), name='current_tos')
]
