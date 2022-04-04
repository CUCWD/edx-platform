"""
URLs for badges API
"""

from django.conf import settings
from django.urls import re_path

from .views import UserBadgeAssertions, CourseBadgeProgressListView, UserBadgeProgressListView

# APP_NAME = 'badges'
urlpatterns = []

# Assertion URLs (User)
urlpatterns += [
    re_path(
        fr'^assertions/user/{settings.USERNAME_PATTERN}/?$',
        UserBadgeAssertions.as_view(),
        name='badges-user-assertions'
    ),
]

# Progress URLs (Course, User)
urlpatterns += [
    re_path(
        fr'^progress/{settings.COURSE_ID_PATTERN}/?$',
        CourseBadgeProgressListView.as_view(),
        name='badges-course-progress'
    ),
    re_path(
        fr'^progress/{settings.COURSE_ID_PATTERN}/user/{settings.USERNAME_PATTERN}/?$',
        UserBadgeProgressListView.as_view(),
        name='badges-course-progress-user'
    ),
]
