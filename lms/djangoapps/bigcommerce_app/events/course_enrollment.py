"""
Events related to how BigCommerce Customers interface with the platform.
Todo: Not used at the moment because this is handled in the LMS dashboard page.
"""

from lms.djangoapps.bigcommerce_app.utils import requires_bigcommerce_enabled


@requires_bigcommerce_enabled
def enroll_paid_bigcommerce_courses(user):  # lint-amnesty, pylint: disable=unused-argument
    """
    Enrolls BigCommerce Customers into platform courses based on products
    (e.g. BigCommerce Courses) paid for.
    """
