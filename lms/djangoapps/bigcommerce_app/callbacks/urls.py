"""
BigCommerce Callback URLs for Single-Click app.
"""

from django.urls import re_path
from django.conf import settings
from django.conf.urls import include, url

from lms.djangoapps.bigcommerce_app.callbacks import views

app_name = 'v1'
urlpatterns = []

urlpatterns += [
    re_path(
        r'auth/$',
        views.BigCommerceAppCallbacks.auth,
        name='auth'
    ),
]

urlpatterns += [
    re_path(
        r'load/$',
        views.BigCommerceAppCallbacks.load,
        name='load'
    ),
]

urlpatterns += [
    re_path(
        r'uninstall/$',
        views.BigCommerceAppCallbacks.uninstall,
        name='uninstall'
    ),
]

urlpatterns += [
    re_path(
        r'remove-user/$',
        views.BigCommerceAppCallbacks.remove_user,
        name='remove-user'
    ),
]
