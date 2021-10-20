"""
BigCommerce related signal handlers.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from lms.djangoapps.bigcommerce_app.events.course_enrollment import enroll_paid_bigcommerce_courses
from lms.djangoapps.bigcommerce_app.utils import bigcommerce_enabled


@receiver(user_logged_in)
def enroll_courses_on_login(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Registers platform users to paid BigCommerce products (e.g. Courses).
    """
    if bigcommerce_enabled:
        enroll_paid_bigcommerce_courses(user)
