"""
Views to show a course's badges.
"""

import six
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.context_processors import csrf
from django.urls import reverse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from courseware.courses import get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.features.course_experience import default_course_url_name
from util.views import ensure_valid_course_key

from . import award_chapter_badges

from lms.djangoapps.badges.api import urls


class CourseBadgesProgressView(View):
    """
    View showing the user's badges for a course.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Displays the user's badges for the specified course.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(course.id)})

        # Award badges to course chapters if they haven't already been done.
        award_chapter_badges(course_id, request)

        # Render the badges list as a fragment
        badges_fragment = CourseBadgesProgressFragmentView().render_to_fragment(request, course_id=course_id)

        # Render the course badges page
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'supports_preview_menu': True,
            'course_url': course_url,
            'badges_fragment': badges_fragment,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        return render_to_response('course_badges/course-badges.html', context)


class CourseBadgesProgressFragmentView(EdxFragmentView):
    """
    Fragment view that shows a user's badges for a course.
    """
    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the user's course badges as a fragment.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)

        language = UserPreference.get_value(request.user, 'pref-lang', default='en')

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'badges_api_url': reverse("badges_api:user_assertions", kwargs={'username': request.user}),
            'language_preference': language,
            'user': User.objects.get(id=request.user.id)
        }
        html = render_to_string('course_badges/course-badges-progress-fragment.html', context)
        fragment = Fragment(html)
        self.add_fragment_resource_urls(fragment)
        return fragment

    def standalone_page_title(self, request, fragment, **kwargs):
        """
        Returns the standalone page title.
        """
        return _('Badges')
