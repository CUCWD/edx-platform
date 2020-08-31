"""
URLs for badges API
"""


from django.conf import settings
from django.conf.urls import include, url

from badges.apis.v1 import views

BADGES_URLS = ([
    url(
        r'^assertions/user/{username}/$'.format(
            username=settings.USERNAME_PATTERN
        ),
        views.UserBadgeAssertions.as_view(), name='user_assertions'
    ),
    url(
        r'^progress/user/{username}/courses/{course_id}/$'.format(
            username=settings.USERNAME_PATTERN,
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.UserBadgeProgressListView.as_view(), name='user_progress'
    ),
], 'badges')

app_name = 'v1'
urlpatterns = [
    url(r'^', include(BADGES_URLS)),
]
