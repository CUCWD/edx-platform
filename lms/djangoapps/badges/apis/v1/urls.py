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
        r'^progress/courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.CourseBadgeProgressListView.as_view(), name='course_progress'
    ),
    url(
        r'^progress/courses/{course_id}/user/{username}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            username=settings.USERNAME_PATTERN
        ),
        views.UserBadgeProgressListView.as_view(), name='course_progress_user'
    ),
], 'badges')

app_name = 'v1'
urlpatterns = [
    url(r'^', include(BADGES_URLS)),
]
