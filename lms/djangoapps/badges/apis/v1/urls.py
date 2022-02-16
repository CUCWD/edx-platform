"""
URLs for badges API
"""

from django.conf import settings
from django.conf.urls import include
from django.urls import path, re_path

from lms.djangoapps.badges.apis.v1 import views

APP_NAME = 'v1'
urlpatterns = []

# Assertion URLs (User)
urlpatterns += [
    re_path(
        fr'^assertions/user/{settings.USERNAME_PATTERN}/$',
        views.UserBadgeAssertions.as_view(),
        name='badges-user-assertions'
    ),
]

# Progress URLs (Course, User)
urlpatterns += [
    re_path(
        fr'^progress/courses/{settings.COURSE_ID_PATTERN}/$',
        views.CourseBadgeProgressListView.as_view(),
        name='badges-course-progress'
    ),
    re_path(
        fr'^progress/courses/{settings.COURSE_ID_PATTERN}/user/{settings.USERNAME_PATTERN}/$',
        views.UserBadgeProgressListView.as_view(),
        name='badges-course-progress-user'
    ),
]
