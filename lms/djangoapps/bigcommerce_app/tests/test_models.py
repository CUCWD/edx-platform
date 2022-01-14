
from django.test import TestCase
from django.test.utils import override_settings

from mock import Mock

from bigcommerce_app.models import (
    Store, 
    AdminUser, 
    StoreAdminUser, 
    Customer, 
    StoreCustomer, 
    StoreCustomerPlatformUser
)

from bigcommerce_app.tests.factories import (
    StoreFactory,
    RandomStoreFactory,
    CustomerFactory,
    StoreCustomerFactory,
    StoreCustomerPlatformUserFactory
)

from student.tests.factories import UserFactory


class StoreCustomerPlatformUserTest(TestCase):
    """
    Test the validation features of StoreCustomerPlatformUser.
    """

    def setUp(self):
        super(StoreCustomerPlatformUserTest, self).setUp()

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

    def tearDown(self):
        super(StoreCustomerPlatformUserTest, self).tearDown()
        Store.objects.all().delete()
        Customer.objects.all().delete()
        StoreCustomer.objects.all().delete()
        StoreCustomerPlatformUser.objects.all().delete()

    def test_locate_store_customer_exists(self):
        """
        Verify that we can get a BigCommerce Store Customer from an existing platform User.
        """

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            self.platform_user
        )
        self.assertEqual(bc_store_customer_id, self.customer.bc_id)
       
    def test_locate_store_customer_not_exists(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User.
        """
        platform_user_not_found = UserFactory.create(email='jane.smith@gmail.com')

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            platform_user_not_found
        )
        self.assertEqual(bc_store_customer_id, None)

    @override_settings(BIGCOMMERCE_APP_STORE_HASH='3r4l2hj8jc')
    def test_locate_customer_multiple_stores(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User registered for two separate BigCommerce storefronts.
        """

        # Create a separate BigCommerce store
        new_store = StoreFactory.create(
            store_hash='3r4l2hj8jc', 
            access_token='38b2kcz5salxe7pgw9zlyaj9b571yky'
        )

        # Create BigCommerce customer account with same email as another store.
        new_customer_same_email = CustomerFactory.create(bc_email='john.doe@gmail.com')

        # Create a store customer mapping for new_store with similar customer email as the setUp store.
        new_store_customer = StoreCustomerFactory.create(
            store=new_store,
            bc_customer=new_customer_same_email
        )

        # Create store customer platform user mapping for new_store, similar customer email, and same platform_user in setUp.
        new_store_customer_platform_user = StoreCustomerPlatformUserFactory(
            bc_store_customer=new_store_customer,
            platform_user=self.platform_user
        )

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            self.platform_user
        )
        self.assertEqual(bc_store_customer_id, new_customer_same_email.bc_id)

    @override_settings(BIGCOMMERCE_APP_STORE_HASH='3r4l2hj8jc')
    def test_locate_customer_multiple_stores_not_exists(self):
        """
        Verify that we cannot get a BigCommerce Store Customer from an existing platform User registered for two separate BigCommerce storefronts.
        """

        # Create a separate BigCommerce store
        new_store = StoreFactory.create(
            store_hash='3r4l2hj8jc', 
            access_token='38b2kcz5salxe7pgw9zlyaj9b571yky'
        )

        # Create BigCommerce customer account with same email as another store.
        new_customer_same_email = CustomerFactory.create(bc_email='john.doe@gmail.com')

        # Create a store customer mapping for new_store with similar customer email as the setUp store.
        new_store_customer = StoreCustomerFactory.create(
            store=new_store,
            bc_customer=new_customer_same_email
        )

        # Don't setup a mapping for this platform user to BigCommerce storefront customer.

        bc_store_customer_id = StoreCustomerPlatformUser.locate_store_customer(
            self.platform_user
        )
        self.assertEqual(bc_store_customer_id, None)