"""
Defines URLs for course badges.
"""

from django.conf.urls import url

from views.course_badges import CourseBadgesFragmentView, CourseBadgesView

urlpatterns = [
    url(
        r'^$',
        CourseBadgesView.as_view(),
        name='openedx.course_badges.home',
    ),
    url(
        r'^badges_fragment$',
        CourseBadgesFragmentView.as_view(),
        name='openedx.course_badges.course_badges_fragment_view',
    ),
]
