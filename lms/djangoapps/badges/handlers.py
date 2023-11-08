"""
Badges related signal handlers.
"""


from django.dispatch import receiver

from common.djangoapps.student.models import EnrollStatusChange
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE
from lms.djangoapps.badges.events.course_meta import award_enrollment_badge
from lms.djangoapps.badges.utils import badges_enabled

from openedx.features.course_experience.utils import get_course_outline_block_tree
from .events.course_section import award_section_badge

@receiver(ENROLL_STATUS_CHANGE)
def award_badge_on_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Awards enrollment badge to the given user on new enrollments.
    """
    if badges_enabled and event == EnrollStatusChange.enroll:
        award_enrollment_badge(user)

def award_section_badges(course_id, request):
    """
    Traverse through the course outline and check each section to see if it needs to assign a badge.
    :return:
    """
    course_block_tree = get_course_outline_block_tree(request, course_id, request.user)
    if not course_block_tree:
        return None

    course_sections = course_block_tree.get('children')
    for section in course_sections:

        if section.get('complete'):
            award_section_badge(request.user, course_id, section['id'])
