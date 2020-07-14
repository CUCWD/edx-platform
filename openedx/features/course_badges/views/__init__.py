

from openedx.features.course_experience.utils import get_course_outline_block_tree
from lms.djangoapps.badges.events.course_section import award_section_badge

def award_chapter_badges(course_id, request):
    """
    Traverse through the course outline and check each chapter to see if it needs to assign a badge.
    :return:
    """
    course_block_tree = get_course_outline_block_tree(request, course_id)
    if not course_block_tree:
        return None

    course_sections = course_block_tree.get('children')

    for section in course_sections:

        if section.get('complete'):
            award_section_badge(course_id, request.user, section['id'])

