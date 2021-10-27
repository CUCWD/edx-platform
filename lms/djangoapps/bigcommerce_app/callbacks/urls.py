"""
BigCommerce Callback URLs for Single-Click app.
"""

# from django.urls import re_path
from django.conf import settings
from django.conf.urls import include, url

# from badges.apis.v1 import views
from bigcommerce_app.callbacks import views

app_name = 'v1'
urlpatterns = []

urlpatterns += [
    url(
        r'auth/$',
        views.BigCommerceAppCallbacks.auth,
        name='auth'
    ),
]

urlpatterns += [
    url(
        r'load/$',
        views.BigCommerceAppCallbacks.load,
        name='load'
    ),
]

urlpatterns += [
    url(
        r'uninstall/$',
        views.BigCommerceAppCallbacks.uninstall,
        name='uninstall'
    ),
]

urlpatterns += [
    url(
        r'remove-user/$',
        views.BigCommerceAppCallbacks.remove_user,
        name='remove-user'
    ),
]
