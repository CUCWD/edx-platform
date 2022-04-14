"""
Define factory classes to be used with the BigCommerce app testing.
"""

import string

from random import random, randrange

import factory


from lms.djangoapps.bigcommerce_app.models import (
    Store,
    AdminUser,
    StoreAdminUser,
    Customer,
    StoreCustomer,
    StoreCustomerPlatformUser
)
from common.djangoapps.student.tests.factories import UserFactory


class StoreFactory(factory.django.DjangoModelFactory):
    """
    Factory for Store
    """

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        model = Store

    store_hash = 'test_store_hash'
    access_token = 'test_access_token'
    scope = 'store_v2_customers_read_only store_v2_default store_v2_orders_read_only ' \
            'store_v2_products_read_only users_basic_information'


class RandomStoreFactory(StoreFactory):
    """
    Same as StoreClassFactory, but randomize the store_hash and access_token
    """
    store_hash = factory.lazy_attribute(lambda _: str(random()).replace('.', '_')[2:18])
    access_token = factory.lazy_attribute(
        lambda _: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(31))
    )


class AdminUserFactory(factory.django.DjangoModelFactory):
    """
    Factory for AdminUser
    """

    class Meta(object):  # lint-amnesty: pylint: disable=missing-class-docstring
        model = AdminUser

    bc_id = factory.lazy_attribute(lambda _: randrange(0, 10000))
    bc_email = factory.Sequence('admin-user-bigcommerce-{0}@gmail.com'.format)  # lint-amnesty, pylint: disable=consider-using-f-string


class StoreAdminUserFactory(factory.django.DjangoModelFactory):
    """
    Factory for StoreAdminUser
    """

    class Meta(object):  # lint-amnesty: pylint: disable=missing-class-docstring
        model = StoreAdminUser

    store = factory.SubFactory(RandomStoreFactory)
    bc_admin_user = factory.SubFactory(AdminUserFactory)
    is_admin = False


class CustomerFactory(factory.django.DjangoModelFactory):
    """
    Factory for Customer
    """

    class Meta(object):  # lint-amnesty: pylint: disable=missing-class-docstring
        model = Customer

    bc_id = factory.lazy_attribute(lambda _: randrange(0, 10000))
    bc_email = factory.Sequence('customer-bigcommerce-{0}@gmail.com'.format)  # lint-amnesty, pylint: disable=consider-using-f-string
    bc_group_id = factory.lazy_attribute(lambda _: randrange(0, 10000))


class StoreCustomerFactory(factory.django.DjangoModelFactory):
    """
    Factory for StoreCustomer
    """

    class Meta(object):  # lint-amnesty: pylint: disable=missing-class-docstring
        model = StoreCustomer

    store = factory.SubFactory(RandomStoreFactory)
    bc_customer = factory.SubFactory(CustomerFactory)


class StoreCustomerPlatformUserFactory(factory.django.DjangoModelFactory):
    """
    Factory for StoreCustomerPlatformUser
    """

    class Meta(object):  # lint-amnesty: pylint: disable=missing-class-docstring
        model = StoreCustomerPlatformUser

    bc_store_customer = factory.SubFactory(StoreCustomerFactory)
    platform_user = factory.SubFactory(UserFactory)
