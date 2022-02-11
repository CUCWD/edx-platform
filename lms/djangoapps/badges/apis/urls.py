"""
Badges API URLs.
"""


from django.conf.urls import include, url

APP_NAME = 'badges'
urlpatterns = [
    url(r'^v1/', include('badges.apis.v1.urls')),
]
