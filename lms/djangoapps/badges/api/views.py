"""
API views for badges
"""
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import serializers

from badges.models import BadgeAssertion, BlockEventBadgesConfiguration
from openedx.core.djangoapps.user_api.permissions import is_field_shared_factory
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)
from openedx.core.lib.api.serializers import CourseKeyField, UsageKeyField

from .serializers import BadgeAssertionSerializer, BlockEventBadgesConfigurationSerializer

from django.contrib.auth.models import User
from branding import api as branding_api


class InvalidCourseKeyError(APIException):
    """
    Raised the course key given isn't valid.
    """
    status_code = 400
    default_detail = "The course key provided was invalid."


class UserBadgeAssertions(generics.ListAPIView):
    """
    ** Use cases **

        Request a list of assertions for a user, optionally constrained to a course.

    ** Example Requests **

        GET /api/badges/v1/assertions/user/{username}/

    ** Response Values **

        Body comprised of a list of objects with the following fields:

        * badge_class: The badge class the assertion was awarded for. Represented as an object
          with the following fields:
            * slug: The identifier for the badge class
            * issuing_component: The software component responsible for issuing this badge.
            * display_name: The display name of the badge.
            * course_id: The course key of the course this badge is scoped to, or null if it isn't scoped to a course.
            * description: A description of the award and its significance.
            * criteria: A description of what is needed to obtain this award.
            * image_url: A URL to the icon image used to represent this award.
        * image_url: The baked assertion image derived from the badge_class icon-- contains metadata about the award
          in its headers.
        * assertion_url: The URL to the OpenBadges BadgeAssertion object, for verification by compatible tools
          and software.

    ** Params **

        * slug (optional): The identifier for a particular badge class to filter by.
        * issuing_component (optional): The issuing component for a particular badge class to filter by
          (requires slug to have been specified, or this will be ignored.) If slug is provided and this is not,
          assumes the issuing_component should be empty.
        * course_id (optional): Returns assertions that were awarded as part of a particular course. If slug is
          provided, and this field is not specified, assumes that the target badge has an empty course_id field.
          '*' may be used to get all badges with the specified slug, issuing_component combination across all courses.

    ** Returns **

        * 200 on success, with a list of Badge Assertion objects.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist

        {
            "count": 7,
            "previous": null,
            "num_pages": 1,
            "results": [
                {
                    "badge_class": {
                        "slug": "special_award",
                        "issuing_component": "openedx__course",
                        "display_name": "Very Special Award",
                        "course_id": "course-v1:edX+DemoX+Demo_Course",
                        "description": "Awarded for people who did something incredibly special",
                        "criteria": "Do something incredibly special.",
                        "image": "http://example.com/media/badge_classes/badges/special_xdpqpBv_9FYOZwN.png"
                    },
                    "image_url": "http://badges.example.com/media/issued/cd75b69fc1c979fcc1697c8403da2bdf.png",
                    "assertion_url": "http://badges.example.com/public/assertions/07020647-e772-44dd-98b7-d13d34335ca6"
                },
            ...
            ]
        }
    """
    serializer_class = BadgeAssertionSerializer
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (is_field_shared_factory("accomplishments_shared"),)

    def filter_queryset(self, queryset):
        """
        Return most recent to least recent badge.
        """
        return queryset.order_by('-created')

    def get_queryset(self):
        """
        Get all badges for the username specified.
        """
        queryset = BadgeAssertion.objects.filter(user__username=self.kwargs['username'])
        provided_course_id = self.request.query_params.get('course_id')
        if provided_course_id == '*':
            # We might want to get all the matching course scoped badges to see how many courses
            # a user managed to get a specific award on.
            course_id = None
        elif provided_course_id:
            try:
                course_id = CourseKey.from_string(provided_course_id)
            except InvalidKeyError:
                raise InvalidCourseKeyError
        elif 'slug' not in self.request.query_params:
            # Need to get all badges for the user.
            course_id = None
        else:
            # Django won't let us use 'None' for querying a ForeignKey field. We have to use this special
            # 'Empty' value to indicate we're looking only for badges without a course key set.
            course_id = CourseKeyField.Empty

        if course_id is not None:
            queryset = queryset.filter(badge_class__course_id=course_id)
        if self.request.query_params.get('slug'):
            queryset = queryset.filter(
                badge_class__slug=self.request.query_params['slug'],
                badge_class__issuing_component=self.request.query_params.get('issuing_component', '')
            )
        return queryset


class UserBadgeProgress(generics.ListAPIView):
    """
    ** Use cases **

        Request a list of block event badge configuration for a user, optionally constrained to a course.

    ** Example Requests **

        GET /api/badges/v1/progress/user/{username}/courses/{course_id}/

    ** Response Values **

        Body comprised of a list of objects with the following fields:

        * course_id: The course key of the course this badge progress is scoped to.
        * block_id: The usage key of the course this badge progress is scoped to.
        * event_type: The block event associated with how the badge was issued.
        * badge_class: The badge class assigned to the course block id. Represented as an object
          with the following fields:
            * slug: The identifier for the badge class
            * issuing_component: The software component responsible for issuing this badge.
            * display_name: The display name of the badge.
            * course_id: The course key of the course this badge is scoped to, or null if it isn't scoped to a course.
            * description: A description of the award and its significance.
            * criteria: A description of what is needed to obtain this award.
            * image_url: A URL to the icon image used to represent this award.
        * assertion: The assertion this badge progress is scoped to.
            * image_url: The baked assertion image derived from the badge_class icon-- contains metadata about the award
              in its headers.
            * assertion_url: The URL to the OpenBadges BadgeAssertion object, for verification by compatible tools
              and software.

    ** Returns **

        * 200 on success, with a list of badge progress objects.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist

        [
            {
                "course_id": "course-v1:edX+DemoX+Demo_Course",
                "block_id": "block-v1:edX+DemoX+Demo_Course+type@chapter+block@dc1e160e5dc348a48a98fa0f4a6e8675",
                "event_type": "chapter_complete",
                "badge_class": {
                    "slug": "special_award",
                    "issuing_component": "openedx__course",
                    "display_name": "Very Special Award",
                    "course_id": "course-v1:edX+DemoX+Demo_Course",
                    "description": "Awarded for people who did something incredibly special",
                    "criteria": "Do something incredibly special.",
                    "image": "http://example.com/media/badge_classes/badges/special_xdpqpBv_9FYOZwN.png"
                },
                "assertion": {
                    "image_url": "http://badges.example.com/media/issued/cd75b69fc1c979fcc1697c8403da2bdf.png",
                    "assertion_url": "http://badges.example.com/public/assertions/07020647-e772-44dd-98b7-d13d34335ca6"
                },
            },
            ...
        ]
    """
    authentication_classes = (
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (is_field_shared_factory("accomplishments_shared"),)


    def list(self, request, username, course_id, *args, **kwargs):

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.warning('Course ID string "%s" is not valid', course_id)
            return Response(
                status=404,
                data={'error_code': 'course_id_not_valid'}
            )

        progress_to_show = []

        for blockEventBadgeConfig in BlockEventBadgesConfiguration.config_for_block_event(
            course_id=course_key, event_type='chapter_complete'
        ):
            block_event_assertion = None
            if blockEventBadgeConfig.badge_class:
                user_course_assertions = BadgeAssertion.assertions_for_user(User.objects.get(username=username),
                                                                            course_id=course_key)
                for assertion in user_course_assertions:
                    if assertion.badge_class == blockEventBadgeConfig.badge_class:
                        block_event_assertion = assertion
                        pass

            progress_to_show.append(
                {
                    "course_id": CourseKeyField(source='course_key').to_representation(course_key),
                    "block_id": UsageKeyField(source='usage_key').to_representation(blockEventBadgeConfig.usage_key),
                    "event_type": blockEventBadgeConfig.event_type,
                    "badge_class": {
                        "slug": blockEventBadgeConfig.badge_class.slug,
                        "issuing_component": blockEventBadgeConfig.badge_class.issuing_component,
                        "display_name": blockEventBadgeConfig.badge_class.display_name,
                        "course_id": CourseKeyField(source='course_key').to_representation(blockEventBadgeConfig.badge_class.course_id),
                        "description": blockEventBadgeConfig.badge_class.description,
                        "criteria": blockEventBadgeConfig.badge_class.criteria,
                        "image": branding_api.get_base_url(request.is_secure()) +
                                    serializers.ImageField(source='image').to_representation(
                                        blockEventBadgeConfig.badge_class.image),
                    },
                    "assertion": {
                        "image_url": (block_event_assertion.image_url if block_event_assertion else ""),
                        "assertion_url": (block_event_assertion.assertion_url if block_event_assertion else ""),
                    },
                }
            )

        return Response(progress_to_show)

