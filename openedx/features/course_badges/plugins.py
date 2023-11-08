"""
Platform plugins to support course bookmarks.
"""

from lms.djangoapps.badges.utils import badges_enabled
from django.conf import settings
from django.utils.translation import ugettext_noop

from lms.djangoapps.courseware.tabs import EnrolledTab
from lms.djangoapps.courseware.courses import get_course_by_id

class CourseBadgesTab(EnrolledTab):
    """
    The course bookmarks tool.
    """
    name = 'badges_progress'
    type = 'badges_progress'
    # priority = None
    title = ugettext_noop('Badges')
    view_name = 'openedx.course_badges.progress'
    # tab_id = 'openedx.course_badges.progress'
    is_dynamic = True
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

        if not is_feature_enabled():
            return False

        if user and not user.is_authenticated:
            return False

        # Retrieve the Advanced Settings Issue Open Badges (`issue_badges`) field from the CourseFields instance.
        # CourseDescriptorWithMixins will be `course` instance when called from the `^/api/courseware/course/` url.
        # CourseOverview will be `course` instance when called from the `^courses/{}/courseware` url.
        if course.id:
            course_fields = get_course_by_id(course.id)
            return course_fields.issue_badges

        return False

def is_feature_enabled():
    """
    Returns True if the teams feature is enabled.
    """
    return badges_enabled()
