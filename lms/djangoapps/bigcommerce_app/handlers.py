"""
BigCommerce related signal handlers.
Todo: This is not currently used since we handle this directly in the LMS Dashboard page.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from lms.djangoapps.bigcommerce_app.events.course_enrollment import enroll_paid_bigcommerce_courses
from lms.djangoapps.bigcommerce_app.utils import bigcommerce_enabled
# from lms.djangoapps.bigcommerce_app.models import Customer, StoreCustomer


@receiver(user_logged_in)
def enroll_courses_on_login(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Registers platform users to paid BigCommerce products (e.g. Courses).
    """
    if bigcommerce_enabled():
        enroll_paid_bigcommerce_courses(user)


@receiver(user_logged_in)
def store_customer_information(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Save the current logged in user for API calls to BigCommerce.

    Note: Couldn't find a way to find Django logged in user easily.
    """
