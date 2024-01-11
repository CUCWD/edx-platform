"""
BigCommerce Callback URLs for Single-Click app.
"""

from django.urls import re_path

from lms.djangoapps.bigcommerce_app.single_click import views

APP_NAME = 'v1'
urlpatterns = []

urlpatterns += [
    re_path(
        r'index/$',
        views.single_click_index,
        name='index'
    ),
]
