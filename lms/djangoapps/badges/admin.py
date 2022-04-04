"""
Admin registration for Badge Models
"""

import logging
import six

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.badges.exceptions import BlockEventBadgesConfigurationException
from lms.djangoapps.badges.forms import BlockEventBadgesConfigurationForm
from lms.djangoapps.badges.models import (
    BadgeAssertion,
    BadgeClass,
    CourseCompleteImageConfiguration,
    CourseEventBadgesConfiguration,
    BlockEventBadgesConfiguration
)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_experience.utils import get_course_outline_block_tree
from opaque_keys.edx.keys import CourseKey

logger = logging.getLogger(__name__)

class CourseIdFilter(admin.SimpleListFilter):
    """
    Filter schedules to by course id using a dropdown list.
    Used from edx-platform/openedx/core/djangoapps/schedules/admin.py
    """
    template = "dropdown_filter.html"
    title = _("Course Id")
    parameter_name = "course_id"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        self.unused_parameters = params.copy()
        self.unused_parameters.pop(self.parameter_name, None)

    def value(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        value = super().value()
        if value == "None" or value is None:
            return None
        else:
            return CourseKey.from_string(value)

    def lookups(self, request, model_admin):  # lint-amnesty, pylint: disable=unused-argument,missing-function-docstring
        return (
            (overview.id, six.text_type(overview.id)) \
                for overview in CourseOverview.objects.all().order_by('id')
        )

    def queryset(self, request, queryset):  # lint-amnesty, pylint: disable=unused-argument,missing-function-docstring
        value = self.value()
        if value is None:
            return queryset
        else:
            return queryset.filter(course_id=value)

    def choices(self, changelist):  # lint-amnesty, pylint: disable=unused-argument,missing-function-docstring
        yield {
            'selected': self.value() is None,
            'value': None,
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'value': six.text_type(lookup),
                'display': title,
            }

admin.site.register(CourseCompleteImageConfiguration)
admin.site.register(BadgeClass)
admin.site.register(BadgeAssertion)
# Use the standard Configuration Model Admin handler for this model.
admin.site.register(CourseEventBadgesConfiguration, ConfigurationModelAdmin)

SAVE_BLOCKEVENTBADGESCONFIGURATION_FAILURE_MSG_TPL = _(
    'An error occurred while saving the {model} to the BlockEventBadgesConfigurationAdmin. '
    'Please try again. If the error persists, please contact the Engineering Team.'
)
@admin.register(BlockEventBadgesConfiguration)
class BlockEventBadgesConfigurationAdmin(admin.ModelAdmin):
    """
    Admin model for managing block event badge configurations.
    Mapping course modules blocks to badges classes.
    """
    form = BlockEventBadgesConfigurationForm  # ({"course": course_id})
    change_form_template = 'admin/badges/blockeventbadgesconfiguration/change_form_template.html'

    raw_id_fields = ['course_id']

    fields = (
        'course',
        'event_type',
        'badge_class',
        'usage_key'
    )

    request = None

    def get_queryset(self, request):
        """
        Define the `request`, so that, the call to locate the course blocks works properly.
        https://stackoverflow.com/questions/727928/django-admin-how-to-access-the-request-object-in-admin-py-for-list-display-met
        """
        query_set = super().get_queryset(request)
        self.request = request
        return query_set

    @admin.display(empty_value='???')
    def chapter_location_name(self, obj):
        """
        Print out friendly version of the `usage_key` for the `chapter` name.
        """
        if self.request:
            course_blocks = get_course_outline_block_tree(
                self.request, str(obj.course_id), self.request.user
                )

            for block in course_blocks.get('children'):

                # Return unique chapter `display_name` + `block_id`
                if block.get('type') == "chapter" and block.get('id') == str(obj.usage_key):
                    return f"'{block.get('display_name')}' – {obj.usage_key}"

        return obj.usage_key

    list_display = ('course', 'event_type', 'badge_class', 'chapter_location_name')
    list_filter = (CourseIdFilter, 'event_type')
    ordering = ('course', 'event_type', 'badge_class')
    search_fields = ('course__id', 'event_type')

    def save_model(self, request, obj, form, change):
        """
        Try to save the model to the database.
        """
        try:
            super().save_model(request, obj, form, change)
        except BlockEventBadgesConfigurationException:
            logger.exception('An error occurred while saving BlockEventBadgesConfiguration'
                ' in Django Admin for course run [%s].', obj.key)

            msg = SAVE_BLOCKEVENTBADGESCONFIGURATION_FAILURE_MSG_TPL.format(model='course run')
            messages.add_message(request, messages.ERROR, msg)

    def get_form(self, request, obj=None, change=False, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Append the `request` into the form.
        https://stackoverflow.com/questions/54150994/django-how-to-set-the-request-in-the-admin-form
        """
        FooForm = super().get_form(request, obj, **kwargs)  # lint-amnesty, pylint: disable=invalid-name
        class RequestFooForm(FooForm):  # lint-amnesty, pylint: disable=missing-class-docstring
            def __new__(cls, *args, **kwargs):
                # kwargs['request'] = request
                return FooForm(request, *args, **kwargs)

        return RequestFooForm
