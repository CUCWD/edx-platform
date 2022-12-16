"""
Model class for BigCommerce.
"""

import logging

from django.db import models
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user


LOGGER = logging.getLogger(__name__)


class Store(models.Model):
    """
    Specifies a BigCommerce store.
    """
    store_hash = models.CharField(max_length=16, blank=False, unique=True)
    access_token = models.CharField(max_length=128, blank=False)
    scope = models.TextField()

    def __str__(self):
        return (
            f"\n[BigCommerce Store]\n"
            f"Hash: {self.store_hash}\nScope: {self.scope}\nAccess Token: {self.access_token}"
        )

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"


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
        return f"\n[BigCommerce Admin User] – Id: {self.bc_id}\nEmail: {self.bc_email}"

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"


class StoreAdminUser(models.Model):
    """
    Specifies a BigCommerce store mapping with the BigCommerce admin user account.
    """
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)
    bc_admin_user = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    is_admin = models.BooleanField(blank=False, default=False)

    def __str__(self):
        return (
            f"\n[BigCommerce Store Admin User]\n"
            f"Store: {self.store}\nAdmin User: {self.bc_admin_user}\nIs Admin: {self.is_admin}"
        )

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"


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
    bc_group_id = models.IntegerField(blank=True, null=True)
    bc_first_name = models.TextField(blank=True)
    bc_last_name = models.TextField(blank=True)
    bc_postal_code = models.TextField(blank=True)
    bc_country_code = models.TextField(blank=True)

    def __str__(self):
        return (
            f"\n[BigCommerce Customer]"
            f"Id: {self.bc_id} \nEmail: {self.bc_email} \nGroup: {self.bc_group_id} \n"
            f"Full Name: {self.bc_first_name} {self.bc_last_name} \n"
            f"Postal Code: {self.bc_postal_code} \n"
            f"Country Code: {self.bc_country_code}"
        )

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"


class StoreCustomer(models.Model):
    """
    Specifies a BigCommerce store mapping with the BigCommerce customer account.
    """
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)
    bc_customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f"\n[BigCommerce Store Customer] – {self.store}\nCustomer: {self.bc_customer}"

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"


class StoreCustomerPlatformUser(models.Model):
    """
    Specifies a BigCommerce store customer mapping with the platform user account.
    """
    bc_store_customer = models.ForeignKey(StoreCustomer, on_delete=models.CASCADE)
    platform_user = models.ForeignKey(User, on_delete=models.CASCADE)

    @classmethod
    def locate_store_customer(cls, store_hash, platform_user):
        """
        Returns a BigCommerce user for a store.
        """

        platform_user_store_customers = cls.objects.filter(platform_user=platform_user)

        if store_hash:
            bc_site_store = Store.objects.get(store_hash=store_hash)

            if bc_site_store:
                for platform_store_customer in platform_user_store_customers:
                    if platform_store_customer.bc_store_customer.store.store_hash == \
                       bc_site_store.store_hash:
                        LOGGER.info(
                            "Located %s from %s for %s platform account",
                            platform_store_customer.bc_store_customer.bc_customer,
                            store_hash,
                            platform_user
                        )
                        return platform_store_customer.bc_store_customer.bc_customer.bc_id

        LOGGER.error(
            "Could not locate BigCommerce %s Store Customer for %s platform account",
            store_hash,
            platform_user
        )

        return None

    class Meta(object):  # lint-amnesty, pylint: disable=missing-class-docstring
        app_label = "bigcommerce_app"
