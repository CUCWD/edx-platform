import logging

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User

from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

LOGGER = logging.getLogger(__name__)


@python_2_unicode_compatible
class Store(models.Model):
    """
    Specifies a BigCommerce store.
    """
    store_hash = models.CharField(max_length=16, blank=False, unique=True)
    access_token = models.CharField(max_length=128, blank=False)
    scope = models.TextField()

    def __str__(self):
        return u"Hash: {store_hash}\nScope: {scope}\nAccess Token: {access_token}".format(
            store_hash=self.store_hash,
            scope=self.scope,
            access_token=self.access_token
        )

    class Meta(object):
        app_label = "bigcommerce_app"

    
@python_2_unicode_compatible
class AdminUser(models.Model):
    """
    Specifies a BigCommerce store user.
    """
    bc_id = models.IntegerField(blank=False)
    bc_email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=False,
    )

    def __str__(self):
        return u"Id: {id}\nEmail: {email}".format(
            id=self.bc_id,
            email=self.bc_email
        )

    class Meta(object):
        app_label = "bigcommerce_app"


@python_2_unicode_compatible
class StoreAdminUser(models.Model):
    """
    Specifies a BigCommerce store mapping with the BigCommerce admin user account.
    """
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)
    bc_admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    is_admin = models.BooleanField(blank=False, default=False)

    def __str__(self):
        return u"Store: {bc_store}\nAdmin User: {admin_user}\nIs Admin: {is_admin}".format(
            bc_store=self.store,
            admin_user=self.bc_admin_user,
            is_admin=self.is_admin
        )

    class Meta(object):
        app_label = "bigcommerce_app"
        

@python_2_unicode_compatible
class Customer(models.Model):
    """
    Specifies a BigCommerce store user.
    """
    bc_id = models.IntegerField(blank=False)
    bc_email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=False,
    )
    bc_group_id = models.IntegerField(blank=False)

    def __str__(self):
        return u"Id: {id}\nEmail: {email}\nGroup: {group_id}".format(
            id=self.bc_id,
            email=self.bc_email,
            group_id=self.bc_group_id
        )

    class Meta(object):
        app_label = "bigcommerce_app"


@python_2_unicode_compatible
class StoreCustomer(models.Model):
    """
    Specifies a BigCommerce store mapping with the BigCommerce customer account.
    """
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)
    bc_customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return u"Store: {bc_store}\nCustomer: {bc_customer}".format(
            bc_store=self.store,
            bc_customer=self.bc_customer
        )

    class Meta(object):
        app_label = "bigcommerce_app"


@python_2_unicode_compatible
class StoreCustomerPlatformUser(models.Model):
    """
    Specifies a BigCommerce store customer mapping with the platform user account.
    """
    bc_store_customer = models.ForeignKey(StoreCustomer, on_delete=models.CASCADE)
    platform_user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def locate_store_customer(cls, platform_user):
        """
        Returns a BigCommerce user for a store.
        """

        platform_user_store_customers = cls.objects.filter(platform_user=platform_user)

        store_hash = configuration_helpers.get_value_for_org('BIGCOMMERCE_APP_STORE_HASH', "SITE_NAME", settings.BIGCOMMERCE_APP_STORE_HASH)

        if store_hash:
            bc_site_store = Store.objects.get(store_hash=store_hash)
            
            if bc_site_store:
                for platform_store_customer in platform_user_store_customers:
                    if platform_store_customer.bc_store_customer.store.store_hash == bc_site_store.store_hash:
                        LOGGER.info(
                            u"Located {customer} from {store} for {platform_user} platform account".format(
                                customer=platform_store_customer.bc_store_customer.bc_customer, store=store_hash, platform_user=platform_user
                            )
                        )
                        return platform_store_customer.bc_store_customer.bc_customer.bc_id

        LOGGER.error(
            u"Could not locate BigCommerce {store} Store Customer for {platform_user} platform account".format(
                store=store_hash, platform_user=platform_user
            )
        )

        return None


    class Meta(object):
        app_label = "bigcommerce_app"
