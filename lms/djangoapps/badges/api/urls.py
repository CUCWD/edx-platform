"""
URLs for badges API
"""
from django.conf import settings
from django.conf.urls import url

from .views import UserBadgeAssertions, CourseBadgeProgress, UserBadgeProgress

urlpatterns = [
    url('^assertions/user/' + settings.USERNAME_PATTERN + '/$', UserBadgeAssertions.as_view(), name='user_assertions'),
    url(
        r'^progress/courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN
        ),
        CourseBadgeProgress.as_view(), name='course_progress'
    ),
    url(
        r'^progress/courses/{course_id}/user/{username}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            username=settings.USERNAME_PATTERN
        ),
        UserBadgeProgress.as_view(), name='course_progress_user'
    ),
]
