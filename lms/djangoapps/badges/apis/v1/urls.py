"""
URLs for badges API
"""

from django.urls import re_path
from django.conf import settings
from django.conf.urls import include, url

from badges.apis.v1 import views

app_name = 'v1'
urlpatterns = []

urlpatterns += [
    re_path(
        r'assertions/user/{username}$'.format(
            username=settings.USERNAME_PATTERN
        ),
        views.UserBadgeAssertions.as_view(),
        name='badges-user-assertions'
    ),
]

urlpatterns += [
    re_path(
        r'progress/courses/{course_id}$'.format(
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.CourseBadgeProgressListView.as_view(),
        name='badges-course-progress'
    ),
]

urlpatterns += [
    re_path(
        r'progress/courses/{course_id}/user/{username}$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            username=settings.USERNAME_PATTERN
        ),
        views.UserBadgeProgressListView.as_view(),
        name='badges-course-progress-user'
    ),
]
