"""
Platform plugins to support course bookmarks.
"""

from badges.utils import badges_enabled
from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab


class CourseBadgesTab(EnrolledTab):
    """
    The course bookmarks tool.
    """
    name = 'course_badges'
    type = 'course_badges'
    # priority = None
    title = ugettext_noop('Badges')
    view_name = 'openedx.course_badges.home'
    # tab_id = 'openedx.course_badges.home'
    is_default = True
    is_movable = True
    is_hideable = True

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the badges feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): the user interacting with the course
        """
        if not super(CourseBadgesTab, cls).is_enabled(course, user=user):
            return False

        if not is_feature_enabled(course):
            return False

        if user and not user.is_authenticated:
            return False

        return course.issue_badges


def is_feature_enabled(course):
    """
    Returns True if the teams feature is enabled.
    """
    return badges_enabled()
