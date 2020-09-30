"""
API views for badges
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from edx_rest_framework_extensions import permissions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics, status
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments import data as enrollment_data
from openedx.core.djangoapps.user_api.accounts.api import visible_fields
from openedx.core.lib.api import permissions as permissions_openedx
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.serializers import (
    CourseKeyField as CourseKeyFieldSerializer,
    UsageKeyField as UsageKeyFieldSerializer
)
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.features.course_experience.utils import get_course_outline_block_tree

from branding import api as branding_api
from student.models import CourseEnrollment

from badges.models import BadgeAssertion, BlockEventBadgesConfiguration
from .serializers import BadgeAssertionSerializer, BlockEventBadgesConfigurationSerializer

USER_MODEL = get_user_model()

log = logging.getLogger(__name__)

class InvalidCourseKeyError(APIException):
    """
    Raised the course key given isn't valid.
    """
    status_code = 400
    default_detail = "The course key provided was invalid."

@view_auth_classes()
class UserBadgeAssertions(generics.ListAPIView):
    """
    **Use Cases**

        Request a list of assertions for a user, optionally constrained to a course.

    **Example Requests**

        GET /api/badges/v1/assertions/user/{username}/

    **Response Values**

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

    **Params**

        * slug (optional): The identifier for a particular badge class to filter by.
        * issuing_component (optional): The issuing component for a particular badge class to filter by
          (requires slug to have been specified, or this will be ignored.) If slug is provided and this is not,
          assumes the issuing_component should be empty.
        * course_id (optional): Returns assertions that were awarded as part of a particular course. If slug is
          provided, and this field is not specified, assumes that the target badge has an empty course_id field.
          '*' may be used to get all badges with the specified slug, issuing_component combination across all courses.

    **Returns**

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
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

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

@view_auth_classes()
class BadgeProgressViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    course_section_mapping = {}

    def _get_single_user_badge_progress(self, course_key, username=None):
        """
        Return badge progress response for a single user for a course.
        """
        progress_response = []

        if not username:
            return progress_response
            # if 'username' in request.GET:
            #     username = request.GET.get('username')
            # else:
            #     username = request.user.username

        if not enrollment_data.get_course_enrollment(username, str(course_key)):
            raise CourseEnrollment.DoesNotExist

        progress_user = USER_MODEL.objects.get(username=username)

        # Traverse through all course chapter blocks and check to see if a user has a badge assertion.
        for block_event_badge_config in BlockEventBadgesConfiguration.config_for_block_event(
                course_id=course_key, event_type='chapter_complete'
        ):
            block_event_assertion = None
            if block_event_badge_config.badge_class:
                user_course_assertions = BadgeAssertion.assertions_for_user(progress_user, course_id=course_key)
                for assertion in user_course_assertions:
                    if assertion.badge_class == block_event_badge_config.badge_class:
                        block_event_assertion = assertion
                        pass

            progress_response.append(self._make_badge_progress_response(
                course_key, block_event_badge_config, block_event_assertion
            ))

        return progress_response

    def _get_course_badge_progress(self, course_key):
        """
        Return badge progress response for a course.
        """
        progress_response = []

        enrollments_in_course = enrollment_data.get_user_enrollments(course_key)

        # paged_enrollments = self.paginator.paginate_queryset(
        #     enrollments_in_course, self.request, view=self
        # )
        enrolled_users = (enrollment.user for enrollment in enrollments_in_course) # paged_enrollments)

        for user in enrolled_users:
            progress_response.append({
                "user_id": user.id,
                "user_name": user.username,
                "name": user.profile.name,
                "email": user.email,
                "progress": self._get_single_user_badge_progress(course_key, user.username)
            })

        return progress_response

    def _make_badge_progress_response(self, course_key, block_event_badge_config, block_event_assertion):
        """
        Return JSON response for course block id based on configuration and assertion information.
        """
        return {
            "course_id": CourseKeyFieldSerializer(source='course_key').to_representation(course_key),
            "block_id": UsageKeyFieldSerializer(source='usage_key').to_representation(block_event_badge_config.usage_key),
            "block_display_name": self.course_section_mapping.get(UsageKeyFieldSerializer(source='usage_key').to_representation(block_event_badge_config.usage_key), '').get('display_name', ''),
            "block_order": self.course_section_mapping.get(UsageKeyFieldSerializer(source='usage_key').to_representation(block_event_badge_config.usage_key), '').get('block_order', ''),
            "event_type": block_event_badge_config.event_type,
            "badge_class": {
                "slug": block_event_badge_config.badge_class.slug,
                "issuing_component": block_event_badge_config.badge_class.issuing_component,
                "display_name": block_event_badge_config.badge_class.display_name,
                "course_id": CourseKeyFieldSerializer(source='course_key').to_representation(block_event_badge_config.badge_class.course_id),
                "description": block_event_badge_config.badge_class.description,
                "criteria": block_event_badge_config.badge_class.criteria,
                "image": branding_api.get_base_url(self.request.is_secure()) + serializers.ImageField(source='image').to_representation(block_event_badge_config.badge_class.image),
            },
            "assertion": {
                "issuedOn": (block_event_assertion.data.get('issuedOn', '') if hasattr(block_event_assertion, 'data') else ""),
                "expires": (block_event_assertion.data.get('expires', '') if hasattr(block_event_assertion, 'data') else ""),
                "revoked": (block_event_assertion.data.get('revoked', False) if hasattr(block_event_assertion, 'data') else False),
                "image_url": (block_event_assertion.image_url if block_event_assertion else ""),
                "assertion_url": (block_event_assertion.assertion_url if block_event_assertion else ""),
                "entityId": (block_event_assertion.data.get('entityId', '') if hasattr(block_event_assertion, 'data') else ""),
                "recipient": {
                    "plaintextIdentity": (block_event_assertion.user.email if block_event_assertion else ""),
                },
                "issuer": (block_event_assertion.assertion_issuer() if block_event_assertion else {
                    "entityType": "",
                    "entityId": "",
                    "openBadgeId": "",
                    "name": "",
                    "image": "",
                    "email": "",
                    "description": "",
                    "url": "",
                }),
            },
        }

    # def perform_authentication(self, request):
    #     """
    #     Ensures that the user is authenticated (e.g. not an AnonymousUser).
    #     """
    #     super(BadgeProgressViewMixin, self).perform_authentication(request)
    #     if request.user.is_anonymous():
    #         raise AuthenticationFailed

@view_auth_classes()
class CourseBadgeProgressListView(BadgeProgressViewMixin, APIView):
    """
    REST API endpoints for listing all users in a course badge progress.

    ** Use cases **

        Get list of block event badge configuration for a course for all users who are enrolled.
        The currently logged-in user may request all enrolled user's badge progress information if they are allowed.
    
    ** Example Requests **
    
        GET /api/badges/v1/progress/courses/{course_id}/
        GET /api/badges/v1/progress/courses/?course_id={course_id}
    
    ** GET Parameters **
    
        A GET request may include the following parameters.
        * course_id: (required) A string representation of a Course ID.
    
    ** Response Values **
    
        Body comprised of a list of objects with the following fields:
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
    
        * 200 on success, with a list of users with badge progress objects.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist
        [
            {
                "user_id": 50,
                "user_name": "JohnDoe",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "progress": [
                    {
                        "course_id": "course-v1:edX+DemoX+Demo_Course",
                        "block_id": "block-v1:edX+DemoX+Demo_Course+type@chapter+block@dc1e160e5dc348a48a98fa0f4a6e8675",
                        "block_display_name": "Example Week 1: Getting Started",
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
                            "issuedOn": "2019-04-20T02:43:06.566955Z",
                            "expires": "2019-04-30T00:00:00.000000Z",
                            "revoked": false,
                            "image_url": "http://badges.example.com/media/issued/cd75b69fc1c979fcc1697c8403da2bdf.png",
                            "assertion_url": "http://badges.example.com/public/assertions/07020647-e772-44dd-98b7-d13d34335ca6",
                            "recipient": {
                                "plaintextIdentity": "john.doe@example.com",
                            },
                            "issuer": {
                                "entityType": "Issuer",
                                "entityId": "npqlh0acRFG5pKKbnb4SRg",
                                "openBadgeId": "https://api.badgr.io/public/issuers/npqlh0acRFG5pKKbnb4SRg",
                                "name": "EducateWorkforce",
                                "image": "https://media.us.badgr.io/uploads/issuers/issuer_logo_77bb4498-838b-45b7-8722-22878fedb5e8.svg",
                                "email": "cucwd.developer@gmail.com",
                                "description": "An online learning solution offered with partnering 2-year colleges to help integrate web and digital solutions into their existing courses. The platform was designed by multiple instructional design, usability, and computing experts to include research-based learning features.",
                                "url": "https://ew-localhost.com",
                            },
                        },
                    },
                    ...
                ]
            },
            ...
        ]
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS, permissions_openedx.IsMasterCourseStaffInstructor)

    # required_scopes = ['badges:read']

    def get(self, request, course_id=None, *args, **kwargs):

        if not course_id:
            course_id = request.GET.get('course_id')

        # Validate course exists with provided course_id
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        if not CourseOverview.get_from_id(course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=course_id),
                error_code='course_does_not_exist'
            )

        self.course_section_mapping = _get_course_section_mapping(request, course_id)

        # if username:
        #     # If there is a username passed, get badge progress for a single user
        #     try:
        #         return Response(self._get_single_user_badge_progress(course_key, username))
        #     except USER_MODEL.DoesNotExist:
        #         raise self.api_error(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             developer_message='The user matching the requested username does not exist.',
        #             error_code='user_does_not_exist'
        #         )
        #     except CourseEnrollment.DoesNotExist:
        #         raise self.api_error(
        #             status_code=status.HTTP_404_NOT_FOUND,
        #             developer_message='The user matching the requested username is not enrolled in this course',
        #             error_code='user_not_enrolled'
        #         )
        # else:
        # If no username passed, get paginated list of grades for all users in course
        return Response(self._get_course_badge_progress(course_key))

@view_auth_classes()
class UserBadgeProgressListView(BadgeProgressViewMixin, APIView):
    """
    REST API endpoints for listing user badge progress.
    
    **Use Cases**

        Get list of block event badge configuration for a course for all users or single user who are enrolled. 
        The currently logged-in user may request all enrolled user's badge progress information if they are allowed.

    **Example Requests**

        GET /api/badges/v1/badges/progress/courses/{course_id}/user/{username}

    **Response Values**

        If the request for information about the user's badges is successful,
        an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a list of objects with the following fields.

        * course_id: The course key of the course this badge progress is scoped to.    
        * block_id: The usage key of the course this badge progress is scoped to.
        * event_type: The block event associated with how the badge was issued.
        * badge_class: The badge class assigned to the course block id. Represented as an object with the following fields:
            * slug: The identifier for the badge class
            * issuing_component: The software component responsible for issuing this badge.
            * display_name: The display name of the badge.
            * course_id: The course key of the course this badge is scoped to, or null if it isn't scoped to a course.
            * description: A description of the award and its significance.
            * criteria: A description of what is needed to obtain this award.
            * image: A URL to the icon image used to represent this award.
        * assertion: The assertion this badge progress is scoped to. Represented as an object with the following fields:
            * image_url: The baked assertion image derived from the badge_class icon-- contains metadata about the award
                in its headers.
            * assertion_url: The URL to the OpenBadges BadgeAssertion object, for verification by compatible tools
                and software.

    **Params**

        The request may include the following parameters.
        * course_id: A string representation of a Course ID.
        * username: A string representation of an user's username passed in the request.

    **Returns**

        * 200 on success, with a list of users with badge progress objects.
        * 403 if a user who does not have permission to masquerade as
        another user specifies a username other than their own.
        * 404 if the specified user does not exist

        [
            {
                "course_id": "course-v1:edX+DemoX+Demo_Course",
                "block_id": "block-v1:edX+DemoX+Demo_Course+type@chapter+block@dc1e160e5dc348a48a98fa0f4a6e8675",
                "block_display_name": "Example Week 1: Getting Started",
                "block_order": 2,
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
                    "issuedOn": "2019-04-20T02:43:06.566955Z",
                    "expires": "2019-04-30T00:00:00.000000Z",
                    "revoked": false,
                    "image_url": "http://badges.example.com/media/issued/cd75b69fc1c979fcc1697c8403da2bdf.png",
                    "assertion_url": "http://badges.example.com/public/assertions/07020647-e772-44dd-98b7-d13d34335ca6"
                    "recipient": {
                        "plaintextIdentity": "edx@example.com",
                    },
                    "issuer": {
                        "entityType": "Issuer",
                        "entityId": "npqlh0acRFG5pKKbnb4SRg",
                        "openBadgeId": "https://api.badgr.io/public/issuers/npqlh0acRFG5pKKbnb4SRg",
                        "name": "EducateWorkforce",
                        "image": "https://media.us.badgr.io/uploads/issuers/issuer_logo_77bb4498-838b-45b7-8722-22878fedb5e8.svg",
                        "email": "cucwd.developer@gmail.com",
                        "description": "An online learning solution offered with partnering 2-year colleges to help integrate web and digital solutions into their existing courses. The platform was designed by multiple instructional design, usability, and computing experts to include research-based learning features.",
                        "url": "https://ew-localhost.com",
                    },
                },
            },
            ...
        ]
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    
    permission_classes = (permissions.JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS,)

    def get(self, request, course_id=None, username=None, *args, **kwargs):  # pylint: disable=arguments-differ        
        """
        Returns a user's viewable badge progress sorted by course name.
        """
        if not username:
            username = request.GET.get('username')

        if not course_id:
            course_id = request.GET.get('course_id')

        # Validate course exists with provided course_id
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        if not CourseOverview.get_from_id(course_key):
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message="Requested grade for unknown course {course}".format(course=course_id),
                error_code='course_does_not_exist'
            )

        self.course_section_mapping = _get_course_section_mapping(request, course_id)

        # if username:
        # If there is a username passed, get badge progress for a single user
        try:
            return Response(self._get_single_user_badge_progress(course_key, username))
        except USER_MODEL.DoesNotExist:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user matching the requested username does not exist.',
                error_code='user_does_not_exist'
            )
        except CourseEnrollment.DoesNotExist:
            raise self.api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user matching the requested username is not enrolled in this course',
                error_code='user_not_enrolled'
            )
        # else:
        #     # If no username passed, get paginated list of grades for all users in course
        #     return Response(self._get_course_badge_progress(course_key))


        # progress_to_show = []
        # progress_to_show.append({
        #     "user_id": 50,
        #     "user_name": "JohnDoe",
        #     "name": "John Doe",
        #     "email": "john.doe@example.com",
        #     "progress": _user_badge_progress(request, "edx", course_id)
        # })
        #
        # return Response(progress_to_show)
        
        # for blockEventBadgeConfig in BlockEventBadgesConfiguration.config_for_block_event(
        #     course_id=course_key, event_type='chapter_complete'
        # ):
        #     block_event_assertion = None
        #     if blockEventBadgeConfig.badge_class:
        #         user_course_assertions = BadgeAssertion.assertions_for_user(user, course_id=course_key)
        #         for assertion in user_course_assertions:
        #             if assertion.badge_class == blockEventBadgeConfig.badge_class:
        #                 block_event_assertion = assertion
        #                 pass

        #     progress_to_show.append(
        #         {
        #             "course_id": CourseKeyFieldSerializer(source='course_key').to_representation(course_key),
        #             "block_id": UsageKeyFieldSerializer(source='usage_key').to_representation(blockEventBadgeConfig.usage_key),
        #             "block_display_name": course_section_mapping.get(UsageKeyFieldSerializer(source='usage_key').to_representation(blockEventBadgeConfig.usage_key), '').get('display_name', ''),
        #             "block_order": course_section_mapping.get(UsageKeyFieldSerializer(source='usage_key').to_representation(blockEventBadgeConfig.usage_key), '').get('block_order', ''),
        #             "event_type": blockEventBadgeConfig.event_type,
        #             "badge_class": {
        #                 "slug": blockEventBadgeConfig.badge_class.slug,
        #                 "issuing_component": blockEventBadgeConfig.badge_class.issuing_component,
        #                 "display_name": blockEventBadgeConfig.badge_class.display_name,
        #                 "course_id": CourseKeyFieldSerializer(source='course_key').to_representation(blockEventBadgeConfig.badge_class.course_id),
        #                 "description": blockEventBadgeConfig.badge_class.description,
        #                 "criteria": blockEventBadgeConfig.badge_class.criteria,
        #                 "image": branding_api.get_base_url(request.is_secure()) +
        #                             serializers.ImageField(source='image').to_representation(
        #                                 blockEventBadgeConfig.badge_class.image),
        #             },
        #             "assertion": {
        #                 "issuedOn": (block_event_assertion.data.get('issuedOn', '') if hasattr(block_event_assertion, 'data') else ""),
        #                 "expires": (block_event_assertion.data.get('expires', '') if hasattr(block_event_assertion, 'data') else ""),
        #                 "revoked": (block_event_assertion.data.get('revoked', False) if hasattr(block_event_assertion, 'data') else False),
        #                 "image_url": (block_event_assertion.image_url if block_event_assertion else ""),
        #                 "assertion_url": (block_event_assertion.assertion_url if block_event_assertion else ""),
        #                 "entityId": (block_event_assertion.data.get('entityId', '') if hasattr(block_event_assertion, 'data') else ""),
        #                 "recipient": {
        #                     "plaintextIdentity": (block_event_assertion.user.email if block_event_assertion else ""),
        #                 },
        #                 "issuer": (block_event_assertion.assertion_issuer() if block_event_assertion else {
        #                     "entityType": "",
        #                     "entityId": "",
        #                     "openBadgeId": "",
        #                     "name": "",
        #                     "image": "",
        #                     "email": "",
        #                     "description": "",
        #                     "url": "",
        #                 }),
        #             },
        #         }
        #     )
        #
        # return Response(progress_to_show)

def _get_course_section_mapping(request, course_id):
    """
    """
    course_section_mapping = {}

    if not course_id:
        return course_section_mapping

    # For all sections in course map the id to the display_name.
    course_block_tree = get_course_outline_block_tree(request, course_id)
    if not course_block_tree:
        return None

    course_sections = course_block_tree.get('children')

    course_section_mapping_id = 0;
    for section in course_sections:
        course_section_mapping.update(
            {
                section['id']:
                    {
                        'block_order': course_section_mapping_id,
                        'display_name': section['display_name']
                    }
            })

        course_section_mapping_id += 1

    return course_section_mapping
