"""
Events related to how BigCommerce Customers interface with the platform.
"""

from lms.djangoapps.bigcommerce_app.utils import requires_bigcommerce_enabled


@requires_bigcommerce_enabled
def enroll_paid_bigcommerce_courses(user):
    """
    Enrolls BigCommerce Customers into platform courses based on products (e.g. BigCommerce Courses) paid for.
    """
    pass
