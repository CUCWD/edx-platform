"""
BigCommerce Callback URLs for Single-Click app.
"""

from django.urls import re_path
from django.conf import settings
from django.conf.urls import include, url

from lms.djangoapps.bigcommerce_app.single_click import views

app_name = 'v1'
urlpatterns = []

urlpatterns += [
    re_path(
        r'index/$',
        views.single_click_index,
        name='index'
    ),
]
