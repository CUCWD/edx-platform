"""
This form allows the administrator to manage friendly block names rather than look at the
block usage_id value.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ugettext_lazy as _
from opaque_keys.edx.keys import UsageKey

from lms.djangoapps.badges.models import BlockEventBadgesConfiguration
from openedx.features.course_experience.utils import get_course_outline_block_tree

CHAPTER_BLOCK_CHOICES = [
    ('', '---------')
]


def load_chapter_block_choices(request, course_id):  # lint-amnesty, pylint: disable=useless-return
    """
    Return choice list for course chapter blocks.
    """
    chapter_options = CHAPTER_BLOCK_CHOICES.copy()

    if request:
        course_blocks = get_course_outline_block_tree(request, course_id, request.user)
        for block in course_blocks.get('children'):

            # Append option if `chapter`
            if block.get('type') == "chapter":
                chapter_options.append(
                    (
                        block.get('id'),
                        block.get('display_name')
                    ))

    return chapter_options


def validate_usage_id(value):
    """
    Validates that a string is lowercase.

    Raises: ValidationError
    """
    if value.strip() and not isinstance(UsageKey.from_string(value), UsageKey):
        raise ValidationError(_(
            "This field may not be blank and must reflect "
            "UsageKey data (e.g. 'block-v1:')"
        ))


class BlockEventBadgesConfigurationForm(forms.ModelForm):
    """
    Admin form for adding a block event badges configuration.
    """

    class Meta:  # lint-amnesty, pylint: disable=missing-class-docstring
        model = BlockEventBadgesConfiguration
        fields = (
            'course',
            'usage_key'
        )

    usage_key = forms.ChoiceField(
        choices=CHAPTER_BLOCK_CHOICES,
        validators=[validate_usage_id],
        required=True,
    )

    def __init__(self, request, *args, **kwargs):
        """
        Assign the `usage_key` field option values. The frontend form pulls data using jQuery
        from the `/api/course_home/outline/{course_id}` LMS endpoint and updating the `usage_key`
        model to match choices is needed. This constructor is called when you click `Save` in the
        Django Admin.
        """
        course_id = None
        try:
            # If args is a QueryDict, then the ModelForm addition request came in as a POST
            # with a course ID string.
            if args and 'course' in args[0] and isinstance(args[0], QueryDict):
                course_id = args[0].get('course')

            if not args and isinstance(kwargs.get('instance'), BlockEventBadgesConfiguration):
                course_id = str(kwargs.get('instance').course_id)

            if course_id is None:
                raise AttributeError("The course_id cannot be None")

        except AttributeError:
            # Don't proceed if the `course_id` is None.
            pass

        super().__init__(*args, **kwargs)

        # Assign the `usage_key` field choices from course `chapter` block {id, name} data.
        if course_id:
            self.fields['usage_key'].choices = load_chapter_block_choices(request, course_id)
