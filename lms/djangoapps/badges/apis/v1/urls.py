"""
URLs for badges API
"""


from django.conf import settings
from django.conf.urls import include
from django.urls import path, re_path

from lms.djangoapps.badges.apis.v1 import views

BADGES_URLS = ([
    re_path(
        fr'^assertions/user/{settings.USERNAME_PATTERN}/$',
        views.UserBadgeAssertions.as_view(), name='user_assertions'
    ),
    re_path(
        fr'^progress/user/{settings.USERNAME_PATTERN}/courses/{settings.COURSE_ID_PATTERN}/$',
        views.UserBadgeProgressListView.as_view(), name='user_progress'
    ),
], 'badges')

APP_NAME = 'v1'
urlpatterns = [
    path('^', include(BADGES_URLS)),
]
