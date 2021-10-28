"""
Utility functions used by the bigcommerce_app.
"""

import logging
from threading import local

from django.conf import settings
from django.http import HttpResponse

from opaque_keys.edx.keys import CourseKey
from common.djangoapps.student.models import CourseEnrollment

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.bigcommerce_app.models import Store, Customer, StoreCustomer, StoreCustomerPlatformUser

import bigcommerce.api as bigcommerce_client
from bigcommerce.resources.products import ProductCustomFields

LOGGER = logging.getLogger(__name__)

def requires_bigcommerce_enabled(function):
    """
    Decorator that bails a function out early if bigcommerce isn't enabled.
    """
    def wrapped(*args, **kwargs):
        """
        Wrapped function which bails out early if bagdes aren't enabled.
        """
        if not bigcommerce_enabled():
            return
        return function(*args, **kwargs)
    return wrapped


def bigcommerce_enabled():
    """
    returns a boolean indicating whether or not BigCommerce app is enabled.
    """
    return configuration_helpers.get_value_for_org('ENABLE_BIGCOMMERCE', "SITE_NAME", settings.FEATURES.get('ENABLE_BIGCOMMERCE', False))

#
# Error handling and helpers
#
def _error_info(e):
    content = ""
    try:  # it's probably a HttpException, if you're using the bigcommerce client
        content += str(e.headers) + "<br>" + str(e.content) + "<br>"
        req = e.response.request
        content += "<br>Request:<br>" + req.url + "<br>" + str(req.headers) + "<br>" + str(req.body)
    except AttributeError as e:  # not a HttpException
        content += "<br><br> (This page threw an exception: {})".format(str(e))
    return content


def internal_server_error(e):
    content = "Internal Server Error: " + str(e) + "<br>"
    content += _error_info(e)
    return HttpResponse(content, status=500)

def _enabled_current_site_provider():
    """
    Helper method to return current provider for the current site.
    """
    import third_party_auth
    from third_party_auth.models import EmailProviderConfig, _PSA_EMAIL_BACKENDS

    if third_party_auth.is_enabled():
        email_backend_names = EmailProviderConfig.key_values('backend_name', flat=True)
        for email_backend_name in email_backend_names:
            provider = EmailProviderConfig.current(email_backend_name)
            if provider.enabled_for_current_site and provider.backend_name in _PSA_EMAIL_BACKENDS:
                return provider

    return None

def client_id():
    """
    Locate the client_id in the current enabled for site EmailProviderConfig.
    """
    try:
        return _enabled_current_site_provider().key
    except Exception as e:
        LOGGER.error(
            u"Could not retrieve `client_id` from current site enabled Third-party Auth Backend.\n{error}".format(error=e)
        )

    return ""


def client_secret():
    """
    Locate the client_secret in the current enabled for site EmailProviderConfig.
    """
    try:
        return _enabled_current_site_provider().secret
    except Exception as e:
        LOGGER.error(
            u"Could not retrieve `client_secret` from current site enabled Third-party Auth Backend.\n{error}".format(error=e)
        )

    return ""


def _store_hash():
    """
    Locate the store_hash in the current enabled for site EmailProviderConfig.
    """
    try:
        return _enabled_current_site_provider().get_setting("STOREFRONT").get("HASH")
    except Exception as e:
        LOGGER.error(
            u"Could not retrieve `Storefront hash_code` from current site enabled Third-party Auth Backend.\n{error}".format(error=e)
        )

    return ""

def store_hash():
    return _store_hash()


def access_token():
    store_hash = _store_hash()
    return Store.objects.filter(store_hash=store_hash).first().access_token


def platform_lms_url():
    return configuration_helpers.get_value("LMS_ROOT_URL", settings.LMS_ROOT_URL)

class BigCommerceAPI():
    """
    Handles talking with the BigCommerceAPI
    """

    def __init__(self):
        self._api_client = bigcommerce_client.BigcommerceApi(client_id=client_id(), store_hash=store_hash(), access_token=access_token())

    @property
    def api_client(self):
        return self._api_client

    @classmethod
    def bcapi_customer_metadata(cls, bc_customer_email):
        """
        Returns Customer information from BigCommerce for current platform user. This is needed for third-party auth to load full name registration form field.

        At the moment this calls V2 of the BigCommerce API which doesn't have an 'id' to make get calls against.
        https://developer.bigcommerce.com/api-reference/store-management/customers-v2/customers/getallcustomers
        """
        # cls._setup_api_client(cls)
        bcapi_client = cls().api_client

        if bcapi_client:
            try:
                customer = bcapi_client.Customers.all(email=bc_customer_email)[0]    
                if customer:

                    LOGGER.info(
                        u"Successfully located BigCommerce {store} Store Customer {customer} meta data".format(
                            store=store_hash(),
                            customer=bc_customer_email
                        )
                    )           
                    
                    return customer
            except Exception as e:
                LOGGER.error(
                    u"Could not get access token from BigCommerce in `auth_callback`"
                )
                return internal_server_error(e)

        LOGGER.error(
            u"Could not locate BigCommerce {store} Store Customer {customer} meta data".format(
                store=store_hash(),
                customer=bc_customer_email
            )
        )
        return {}

    @classmethod
    def bigcommerce_customer_save(cls, payload):
        """
        Returns decode payload from JWT token passed in from BigCommerce third-party-auth complete and saves the customer information on the platform.
        """
        bcapi_client = cls().api_client
        if bcapi_client:
            try:
                user_data = bcapi_client.oauth_verify_payload_jwt(payload, client_secret(), client_id())

                bc_customer = cls.bcapi_customer_metadata(user_data['customer']['email'])

                # Save the BigCommerce Customer for the platform
                try:
                    new_customer, __ = Customer.objects.get_or_create(bc_id=bc_customer.id, bc_email=bc_customer.email)
                    new_customer.bc_group_id = bc_customer.customer_group_id
                    new_customer.bc_first_name = bc_customer.first_name
                    new_customer.bc_last_name = bc_customer.last_name
                    new_customer.save()
                except Exception as e:
                    LOGGER.error(
                        u"Could save BigCommerce Customer {customer}".format(
                            customer=bc_customer.email
                        )
                    )
                    return {}

                # Save the BigCommerce StoreCustomer fro the platform
                store = Store.objects.filter(store_hash=store_hash()).first()
                if store:
                    try:
                        new_store_customer, __ = StoreCustomer.objects.get_or_create(
                            store=store,
                            bc_customer=new_customer
                        )
                        new_store_customer.save()
                    except Exception as e:
                        LOGGER.error(
                            u"Could save BigCommerce StoreCustomer {store_hash} – {customer}".format(
                                store_hash=store_hash(),
                                customer=bc_customer.email
                            )
                        )
                        return {}
                else:
                    LOGGER.error(
                        u"Could not create StoreCustomer for {store} – {customer}.".format(
                            store=store_hash(),
                            customer=new_customer.email
                        )
                    )

                return {
                    'store_hash': store_hash(),
                    'id': new_customer.bc_id,
                    'email': new_customer.bc_email,
                    'group_id': new_customer.bc_group_id,
                    'first_name': new_customer.bc_first_name,
                    'last_name': new_customer.bc_last_name
                }

            except Exception as e:
                LOGGER.error(
                    u"Could not decode JWT payload from BigCommerce Customer."
                )
                return internal_server_error(e)

        return {}

    @classmethod
    def bigcommerce_store_customer_platform_user_save(cls, payload):
        """
        Returns true whether or not the StoreCustomerPlatformUser was saved successfully.
        """
        try:
            platform_user = payload.get('platform_user')

            store = Store.objects.filter(store_hash=store_hash()).first()
            if store:
                try:
                    bc_store_customer = StoreCustomer.objects.filter(
                        store=store,
                        bc_customer__bc_id=payload.get('bc_uid')
                    ).first()

                    bc_store_customer_platform_user, bc_store_customer_platform_user_created = StoreCustomerPlatformUser.objects.get_or_create(
                        bc_store_customer=bc_store_customer,
                        platform_user=platform_user
                    )
                    bc_store_customer_platform_user.save()

                    if bc_store_customer_platform_user_created:
                        return True

                except Exception as e:
                    LOGGER.error(
                        u"Could save StoreCustomerPlatformUser: BigCommerce {bc_customer} – Platform {platform_user}".format(
                            bc_customer=payload.get('bc_uid'),
                            platform_user=platform_user.id
                        )
                    )
            else:
                LOGGER.error(
                    u"Could not locate {store} to make StoreCustomerPlatformUser mapping.".format(
                        store=store_hash()
                    )
                )

        except Exception as e:
            LOGGER.error(
                u"Could not find BigCommerce StoreCustomer."
            )
            return internal_server_error(e)

        return False

    @classmethod
    def get_order_items(cls, customer_id):

        bcapi_client = cls().api_client

        if bcapi_client:
            try:
                orders = bcapi_client.Orders.all(customer_id=customer_id)
            except:
                return

            courses = []

            for order in orders:
                products = bcapi_client.OrderProducts.all(order.id)

                for product in products:
                    product_details = bcapi_client.Products.get(product.product_id)
                    custom_fields = product_details.custom_fields()

                    if custom_fields:
                        for field in custom_fields:
                            if isinstance(field, ProductCustomFields) and field.name == 'Course ID':
                                courses.append(field.text)

            return courses

    @classmethod
    def get_bc_course_enrollments(cls, user):

        try:
            bc_customer_id = StoreCustomerPlatformUser.locate_store_customer(user.id)
        except:
            return

        if bc_customer_id:
            enroll_courses = cls.get_order_items(bc_customer_id)

            if enroll_courses:
                for course_key in enroll_courses:
                    course_key = CourseKey.from_string(course_key)
                    CourseEnrollment.enroll(user, course_key)
