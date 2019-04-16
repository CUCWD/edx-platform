"""
Events which have to do with a user completing a section of content within a course.
"""

from badges.models import BlockEventBadgesConfiguration
from badges.utils import requires_badges_enabled

from opaque_keys.edx.keys import CourseKey, UsageKey

@requires_badges_enabled
def award_section_badge(user, course_id, section_id):
    """
    Awards badges based on the user after the section completion api checks have been checked.

    Todo: It appears that there is no signal for when a course completion event occurs other than just problems type.
      Should a event occur we should listen for the signal using a @receiver decorator and award the badge right away
      for the given section. Right now we are checking on outline and badge courseware tab loads whether or not we need
      to award the section badge.
    """

    badge_class = BlockEventBadgesConfiguration.get_badgeclass_for_chapter_complete(CourseKey.from_string(course_id),
                                                                                    UsageKey.from_string(section_id))

    # Continue without awarding badge if no configuration is found in BlockEventBadgesConfiguration
    if not badge_class:
        return

    # Award badge to user.
    if not badge_class.get_for_user(user):
        badge_class.award(user)


