"""
Admin registration for Badge Models
"""


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from badges.models import BadgeClass, CourseCompleteImageConfiguration, CourseEventBadgesConfiguration, \
    BlockEventBadgesConfiguration

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.keys import CourseKey


class CourseIdFilter(admin.SimpleListFilter):
    """
    Filter schedules to by course id using a dropdown list.
    Used from edx-platform/openedx/core/djangoapps/schedules/admin.py
    """
    template = "dropdown_filter.html"
    title = _("Course Id")
    parameter_name = "course_id"

    def __init__(self, request, params, model, model_admin):
        super(CourseIdFilter, self).__init__(request, params, model, model_admin)
        self.unused_parameters = params.copy()
        self.unused_parameters.pop(self.parameter_name, None)

    def value(self):
        value = super(CourseIdFilter, self).value()
        if value == "None" or value is None:
            return None
        else:
            return CourseKey.from_string(value)

    def lookups(self, request, model_admin):
        return (
            (overview.id, unicode(overview.id)) for overview in CourseOverview.objects.all().order_by('id')
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        else:
            return queryset.filter(course_id=value)

    def choices(self, changelist):  # pylint: disable=unused-argument
        yield {
            'selected': self.value() is None,
            'value': None,
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'value': unicode(lookup),
                'display': title,
            }

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)

@admin.register(BlockEventBadgesConfiguration)
class BlockEventBadgesConfigurationAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'event_type', 'badge_class', 'usage_key')
    list_filter = (CourseIdFilter, 'event_type')
    ordering = ('course_id', 'event_type', 'badge_class')
    search_fields = ('course_id', 'event_type')

