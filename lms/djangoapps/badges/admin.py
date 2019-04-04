"""
Admin registration for Badge Models
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from badges.models import BadgeClass, CourseCompleteImageConfiguration, CourseEventBadgesConfiguration, \
    BlockEventBadgesConfiguration

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)

@admin.register(BlockEventBadgesConfiguration)
class BlockEventBadgesConfigurationAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'event_type', 'badge_class', 'usage_key')
    list_filter = ('course_id', 'event_type')
    ordering = ('course_id', 'event_type', 'badge_class')
    search_fields = ('course_id', 'event_type')

