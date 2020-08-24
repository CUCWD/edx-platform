"""
URLs for badges API
"""


from django.conf import settings
from django.conf.urls import url

from .views import UserBadgeAssertions, UserBadgeProgress

urlpatterns = [
    url('^assertions/user/' + settings.USERNAME_PATTERN + '/$', UserBadgeAssertions.as_view(), name='user_assertions'),
    # url('^progress/user/' + settings.USERNAME_PATTERN + '/$', UserBadgeProgress.as_view(), name='user_progress'),
    url(
        r'^progress/user/{username}/courses/{course_id}/$'.format(
            username=settings.USERNAME_PATTERN,
            course_id=settings.COURSE_ID_PATTERN
        ),
        UserBadgeProgress.as_view(), name='user_progress'
    ),
]
