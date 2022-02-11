"""
URLs for badges API
"""


from django.conf import settings
from django.urls import re_path

from .views import UserBadgeAssertions, UserBadgeProgress

urlpatterns = [
    re_path(fr'^assertions/user/{settings.USERNAME_PATTERN}/$',
        UserBadgeAssertions.as_view(), name='user_assertions'
        ),
    re_path(fr'^assertions/user/{settings.USERNAME_PATTERN}/$',
        UserBadgeAssertions.as_view(), name='user_assertions'
        ),
    # re_path(fr'^progress/user/{settings.USERNAME_PATTERN}/$',
    #     UserBadgeProgress.as_view(), name='user_progress'
    #     ),
    re_path(
        fr'^progress/user/{settings.USERNAME_PATTERN}/courses/{settings.COURSE_ID_PATTERN}/$',
        UserBadgeProgress.as_view(), name='user_progress'
    ),
]
