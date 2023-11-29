"""
Defines URLs for course badges.
"""

from django.urls import re_path  # path
from django.views.generic.base import RedirectView

# from .views.course_badges_home import CourseBadgesHomeFragmentView, CourseBadgesHomeView
from .views.course_badges_progress import CourseBadgesProgressFragmentView, CourseBadgesProgressView

urlpatterns = [
    re_path(
        r'^progress$',
        CourseBadgesProgressView.as_view(),
        name='openedx.course_badges.progress',
    ),
    re_path(
        r'^badges_progress_fragment$',
        CourseBadgesProgressFragmentView.as_view(),
        name='openedx.course_badges.course_badges_progress_fragment_view',
    ),
    # Todo: Should we want to actually have a home page for the Badges MFE we'll need to enable
    # these urls.
    # re_path(
    #     r'^$',
    #     CourseBadgesHomeView.as_view(),
    #     name='openedx.course_badges.home',
    # ),
    # re_path(
    #     r'^badges_home_fragment$',
    #     CourseBadgesHomeFragmentView.as_view(),
    #     name='openedx.course_badges.course_badges_home_fragment_view',
    # ),
    re_path(
        r'^$',
        RedirectView.as_view(pattern_name='openedx.course_badges.progress', permanent=False),
        name='openedx.course_badges.home',
    ),
]
