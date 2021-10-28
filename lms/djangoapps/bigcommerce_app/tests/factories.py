
from random import random, randrange
import string

import json
import factory
from factory import DjangoModelFactory

from lms.djangoapps.bigcommerce_app.models import (
    Store, 
    AdminUser, 
    StoreAdminUser, 
    Customer, 
    StoreCustomer, 
    StoreCustomerPlatformUser
)
from student.tests.factories import UserFactory


class StoreFactory(DjangoModelFactory):
    """
    Factory for Store
    """
    
    class Meta(object):
        model = Store

    store_hash = 'test_store_hash'
    access_token = 'test_access_token'
    scope = 'store_v2_customers_read_only store_v2_default store_v2_orders_read_only store_v2_products_read_only users_basic_information'


class RandomStoreFactory(StoreFactory):
    """
    Same as StoreClassFactory, but randomize the store_hash and access_token
    """
    store_hash = factory.lazy_attribute(lambda _: str(random()).replace('.', '_')[2:18])
    access_token = factory.lazy_attribute(lambda _: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(31)))


class AdminUserFactory(DjangoModelFactory):
    """
    Factory for AdminUser
    """

    class Meta(object):
        model = AdminUser

    bc_id = factory.lazy_attribute(lambda _: randrange(0, 10000))
    bc_email = factory.Sequence(u'admin-user-bigcommerce-{0}@gmail.com'.format)


class StoreAdminUserFactory(DjangoModelFactory):
    """
    Factory for StoreAdminUser
    """

    class Meta(object):
        model = StoreAdminUser

    store = factory.SubFactory(RandomStoreFactory)
    bc_admin_user = factory.SubFactory(AdminUserFactory)
    is_admin = False


class CustomerFactory(DjangoModelFactory):
    """
    Factory for Customer
    """

    class Meta(object):
        model = Customer

    bc_id = factory.lazy_attribute(lambda _: randrange(0, 10000))
    bc_email = factory.Sequence(u'customer-bigcommerce-{0}@gmail.com'.format)
    bc_group_id = factory.lazy_attribute(lambda _: randrange(0, 10000))


class StoreCustomerFactory(DjangoModelFactory):
    """
    Factory for StoreCustomer
    """

    class Meta(object):
        model = StoreCustomer

    store = factory.SubFactory(RandomStoreFactory)
    bc_customer = factory.SubFactory(CustomerFactory)
    

class StoreCustomerPlatformUserFactory(DjangoModelFactory):
    """
    Factory for StoreCustomerPlatformUser
    """

    class Meta(object):
        model = StoreCustomerPlatformUser

    bc_store_customer = factory.SubFactory(StoreCustomerFactory)
    platform_user = factory.SubFactory(UserFactory)
