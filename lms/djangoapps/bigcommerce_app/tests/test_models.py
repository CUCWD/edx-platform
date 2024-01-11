"""
Tests for integration with BigCommerce ecommerce service.
"""

from django.test import TestCase
from django.test.utils import override_settings

from lms.djangoapps.bigcommerce_app.models import (
    Store,
    # AdminUser,
    # StoreAdminUser,
    Customer,
    StoreCustomer,
    StoreCustomerPlatformUser
)

from lms.djangoapps.bigcommerce_app.tests.factories import (
    StoreFactory,
    # RandomStoreFactory,
    CustomerFactory,
    StoreCustomerFactory,
    StoreCustomerPlatformUserFactory
)

from common.djangoapps.student.tests.factories import UserFactory


class StoreCustomerPlatformUserTest(TestCase):
    """
    Test the validation features of StoreCustomerPlatformUser.
    """

    def setUp(self):  # lint-amnesty, pylint: disable=invalid-name
        """
        Setup defaults for BigCommerce store, customer, and platform accounts.
        """

        super().setUp()

        # Create BigCommerce store
        self.store = StoreFactory.create(
            store_hash='1nol3cto8',
            access_token='lwqngxmw4d6yfv8un97ubujr8hc1hg1'
        )

        # Create BigCommerce customer account
        self.customer = CustomerFactory.create(bc_email='john.doe@gmail.com')

        # Create platform user accounts
        self.platform_user = UserFactory.create(email='john.doe@gmail.com')

        # Create a store customer mapping
        self.store_customer = StoreCustomerFactory.create(
            store=self.store,
            bc_customer=self.customer
        )

        # Create store customer platform user mapping
        self.store_customer_platform_user = StoreCustomerPlatformUserFactory(
            bc_store_customer=self.store_customer,
            platform_user=self.platform_user
        )

    def tearDown(self):  # lint-amnesty, pylint: disable=invalid-name
        """
        Remove test objects.
        """

        super().tearDown()
        Store.objects.all().delete()
        Customer.objects.all().delete()
        StoreCustomer.objects.all().delete()
        StoreCustomerPlatformUser.objects.all().delete()

    def test_locate_store_customer_exists(self):
        """
        Verify that we can get a BigCommerce Store Customer from an existing platform User.
        """

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            store_hash=self.store.store_hash,
            platform_user=self.platform_user
        )
        self.assertEqual(bc_store_customer_id, self.customer.bc_id)

    def test_locate_store_customer_not_exists(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User.
        """
        platform_user_not_found = UserFactory.create(email='jane.smith@gmail.com')

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            store_hash=self.store.store_hash,
            platform_user=platform_user_not_found
        )
        self.assertEqual(bc_store_customer_id, None)

    @override_settings(BIGCOMMERCE_APP_STORE_HASH='3r4l2hj8jc')
    def test_locate_customer_multiple_stores(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User
        registered for two separate BigCommerce storefronts.
        """

        # Create a separate BigCommerce store
        new_store = StoreFactory.create(
            store_hash='3r4l2hj8jc',
            access_token='38b2kcz5salxe7pgw9zlyaj9b571yky'
        )

        # Create BigCommerce customer account with same email as another store.
        new_customer_same_email = CustomerFactory.create(bc_email='john.doe@gmail.com')

        # Create a store customer mapping for new_store with similar customer email as the
        # setUp store.
        new_store_customer = StoreCustomerFactory.create(
            store=new_store,
            bc_customer=new_customer_same_email
        )

        # Create store customer platform user mapping for new_store, similar customer email, and
        # same platform_user in setUp.
        new_store_customer_platform_user = StoreCustomerPlatformUserFactory(  # lint-amnesty, pylint: disable=unused-variable
            bc_store_customer=new_store_customer,
            platform_user=self.platform_user
        )

        # Check new store for this customer
        bc_newstore_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            store_hash='3r4l2hj8jc',
            platform_user=self.platform_user
        )
        self.assertEqual(bc_newstore_customer_id, new_customer_same_email.bc_id)

        # Check setup store for this customer
        bc_setupstore_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            store_hash=self.store.store_hash,
            platform_user=self.platform_user
        )
        self.assertNotEqual(bc_setupstore_customer_id, new_customer_same_email.bc_id)

    @override_settings(BIGCOMMERCE_APP_STORE_HASH='3r4l2hj8jc')
    def test_locate_customer_multiple_stores_not_exists(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User
        registered for two separate BigCommerce storefronts.
        """

        # Create a separate BigCommerce store
        new_store = StoreFactory.create(
            store_hash='3r4l2hj8jc',
            access_token='38b2kcz5salxe7pgw9zlyaj9b571yky'
        )

        # Create BigCommerce customer account with same email as another store.
        new_customer_same_email = CustomerFactory.create(bc_email='john.doe@gmail.com')

        # Create a store customer mapping for new_store with similar customer email as the
        # setUp store.
        new_store_customer = StoreCustomerFactory.create(  # lint-amnesty, pylint: disable=unused-variable
            store=new_store,
            bc_customer=new_customer_same_email
        )

        # Don't setup a mapping for this platform user to BigCommerce storefront customer.

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            store_hash='3r4l2hj8jc',
            platform_user=self.platform_user
        )
        self.assertEqual(bc_store_customer_id, None)
