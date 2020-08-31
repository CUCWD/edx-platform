"""
Badges API URLs.
"""


from django.conf.urls import include, url

app_name = 'badges'
urlpatterns = [
    url(r'^v1/', include('badges.apis.v1.urls')),
]
