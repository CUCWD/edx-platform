"""
BigCommerce Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig


class BigCommerceAppConfig(AppConfig):
    """
    Application Configuration for BigCommerce.
    """
    name = u'bigcommerce_app'

    def ready(self):
        """
        Connect signal handlers.
        """
        from . import handlers  # pylint: disable=unused-import
