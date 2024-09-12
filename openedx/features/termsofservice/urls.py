# pylint: disable=missing-module-docstring

from django.urls import path, include

urlpatterns = [
    path('termsofservice/', include('openedx.features.termsofservice.api.v1.urls')),
]
