"""
Admin registration for Badge Models
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from lms.djangoapps.badges.models import (  # pylint: disable=syntax-error
    BadgeAssertion,
    BadgeClass,
    CourseCompleteImageConfiguration,
    CourseEventBadgesConfiguration,
    BlockEventBadgesConfiguration
)

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
admin.site.register(BadgeAssertion)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)

@admin.register(BlockEventBadgesConfiguration)
class BlockEventBadgesConfigurationAdmin(admin.ModelAdmin):
    """
    Admin model for managing block event badge configurations.
    Mapping course modules blocks to badges classes.
    """
    list_display = ('course_id', 'event_type', 'badge_class', 'usage_key')
    list_filter = ('course_id', 'event_type')
    ordering = ('course_id', 'event_type', 'badge_class')
    search_fields = ('course_id', 'event_type')
