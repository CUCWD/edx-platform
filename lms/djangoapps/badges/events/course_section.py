"""
Events which have to do with a user completing a section of content within a course.
"""

from badges.models import BadgeClass, CourseEventBadgesConfiguration
from badges.models import BlockEventBadgesConfiguration
from badges.utils import requires_badges_enabled

from opaque_keys.edx.keys import CourseKey, UsageKey

# def award_badge(config, count, user):
#     """
#     Given one of the configurations for enrollments or completions, award
#     the appropriate badge if one is configured.
#
#     config is a dictionary with integer keys and course keys as values.
#     count is the key to retrieve from this dictionary.
#     user is the user to award the badge to.
#
#     Example config:
#         {3: 'slug_for_badge_for_three_enrollments', 5: 'slug_for_badge_with_five_enrollments'}
#     """
#     slug = config.get(count)
#     if not slug:
#         return
#     # badge_class = BadgeClass.get_badge_class(
#     #     slug=slug, issuing_component='openedx__course', create=False,
#     # )
#     #
#     badge_class = BlockEventBadgesConfiguration.get_badgeclass_for_block_event(
#         course_id=course_id, event_type="chapter_complete"
#     )
#
#     if not badge_class:
#         return
#     if not badge_class.get_for_user(user):
#         badge_class.award(user)


def award_section_badge(course_id, user, section_id):
    """
    Awards badges based on the user after the section completion api checks have been checked.
    """

    badge_class = BlockEventBadgesConfiguration.get_badgeclass_for_chapter_complete(CourseKey.from_string(course_id),
                                                                                    UsageKey.from_string(section_id))

    # Continue without awarding badge if no configuration is found in BlockEventBadgesConfiguration
    if not badge_class:
        return

    # Award badge to user.
    if not badge_class.get_for_user(user):
        badge_class.award(user)

    # config = CourseEventBadgesConfiguration.current().enrolled_settings
    # enrollments = user.courseenrollment_set.filter(is_active=True).count()

