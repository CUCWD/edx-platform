"""
API views for badges
"""

import logging

from django.http import HttpResponse
from django.shortcuts import redirect, reverse
# from django.urls import reverse

from bigcommerce.api import BigcommerceApi
from bigcommerce_app.utils import internal_server_error, client_id, client_secret, platform_lms_url
from bigcommerce_app.models import Store, AdminUser, StoreAdminUser

LOGGER = logging.getLogger(__name__)


class BigCommerceAppCallbacks():
    """
    Handles all the Single-Click app (SCa) Callback Urls
    - Auth Callback URL
    - Load Callback URL
    - Uninstall Callback URL
    - Remove User Callback URL (when SCa has Multiple Users enabled)

    These callback URLs will be called during the OAuth registration process, or when the user uninstalls your app. Importantly, communication with these endpoints must be done over HTTPS.
    """

    @classmethod
    def auth(cls, request):
        """
        The GET request to your app’s auth callback URL contains a temporary code that can be exchanged for a permanent access_token. It also includes a unique value that identifies the store installing or updating your app, as well as authorized scopes.
        

        https://developer.bigcommerce.com/api-docs/apps/guide/auth#receiving-the-get-request
        """
        LOGGER.info(
            u"Initiated single-click app `auth_callback` from BigCommerce"
        )

        code = request.GET.get('code')
        context = request.GET.get('context')
        scope = request.GET.get('scope')
        store_hash = context.split('/')[1]

        # Should be same as the BigCommerce Single-Click app Auth Callback URL
        auth_redirect = "{lms_root_url}{bcapp_auth_callback}".format(
            lms_root_url=platform_lms_url(),
            bcapp_auth_callback=reverse('bigcommerce_app_callbacks:auth')).rstrip("/")

        # Fetch a permanent oauth token. This will throw an exception on error,
        # which will get caught by our error handler above.
        client = BigcommerceApi(client_id=client_id(), store_hash=store_hash)

        try:
            token = client.oauth_fetch_token(client_secret(), code, context, scope, auth_redirect)
            bc_store_admin_user_id = token['user']['id']
            bc_store_admin_email = token['user']['email']
            access_token = token['access_token']
        except Exception as e:
            LOGGER.error(
                u"Could not get access token from BigCommerce in `auth_callback`"
            )
            return internal_server_error(e)

        # Create or update store
        store, store_created = Store.objects.get_or_create(store_hash=store_hash)
        store.access_token = access_token
        store.scope = scope
        store.save()
        # If the app was installed before, make sure the old admin user is no longer marked as the admin
        if not store_created:
            old_store_admin_user = StoreAdminUser.objects.filter(store__id=store.id, is_admin=True).first()
            if old_store_admin_user:
                old_store_admin_user.is_admin = False
                old_store_admin_user.save()            

        # Create or update global BigCommerce store admin user
        admin_user, __ = AdminUser.objects.get_or_create(bc_id=bc_store_admin_user_id)
        admin_user.bc_email = bc_store_admin_email
        admin_user.save()

        store_admin_user, store_admin_user_created = StoreAdminUser.objects.get_or_create(store_id=store.id, bc_admin_user_id=admin_user.id)
        if store_admin_user_created:
            store_admin_user.is_admin = True
        store_admin_user.save()

        # response = redirect(platform_lms_url() + "/bigcommerce/single-click/index/")
        # reverse("badges_api:v1:badges-user-assertions", kwargs={'username': request.user})
        response = redirect(reverse("bigcommerce_app_single_click:index") + '?bc_storeadminuserid={id}'.format(id=store_admin_user.bc_admin_user.bc_id))
        
        # Todo: This doesn't work at the moment.
        # response.set_cookie('bc_storeadminuserid', store_admin_user.bc_admin_user.bc_id, secure=True, max_age=1000)

        return response


    @classmethod
    def load(cls, request):
        """
        BigCommerce sends a GET request to your app’s load URL when the store owner or user clicks to load the app.

        The steps to handle this callback are as follows:

        1. Verify the signed payload (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#verifying-the-signed-payload).
        2. Identify the user (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#identifying-users).
        3. Respond with HTML for the control panel iFrame.

        https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#load-callback

        Todo: Need to implement this for BigCommerce admin interface.
        """
        LOGGER.info(
            u"Initiated single-click app `load_callback` from BigCommerce"
        )

        # Decode and verify payload
        payload = request.GET.get('signed_payload_jwt')
        try:
            user_data = BigcommerceApi.oauth_verify_payload_jwt(payload, client_secret(), client_id())
            bc_store_admin_user_id = user_data['user']['id']
            bc_store_admin_email = user_data['user']['email']
            store_hash = user_data['sub'].split('stores/')[1]
        except Exception as e:
            LOGGER.error(
                u"Could not get access token from BigCommerce in `auth_callback`"
            )
            return internal_server_error(e)

        # Lookup store
        store = Store.objects.filter(store_hash=store_hash).first()
        if store is None:
            return HttpResponse("Store not found!", status=401)

        # Lookup user and create if doesn't exist (this can happen if you enable multi-user
        # when registering your app)

        # Create or update global BigCommerce store admin user
        admin_user, __ = AdminUser.objects.get_or_create(bc_id=bc_store_admin_user_id)
        admin_user.bc_email = bc_store_admin_email
        admin_user.save()

        store_admin_user, __ = StoreAdminUser.objects.get_or_create(store_id=store.id, bc_admin_user_id=admin_user.id)
        store_admin_user.save()

        # response = redirect(platform_lms_url() + "/bigcommerce/single-click/index/")
        # reverse("badges_api:v1:badges-user-assertions", kwargs={'username': request.user})
        response = redirect(reverse("bigcommerce_app_single_click:index") + '?bc_storeadminuserid={id}'.format(id=store_admin_user.bc_admin_user.bc_id))
        
        # Todo: This doesn't work at the moment.
        # response.set_cookie('bc_storeadminuserid', store_admin_user.bc_admin_user.bc_id, secure=True, max_age=1000)

        return response


    @classmethod
    def uninstall(cls, request):
        """
        BigCommerce sends a GET request to your app’s uninstall URL when the store owner clicks to uninstall the app.

        The steps to handle this callback are as follows:

        1. Verify the signed payload (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#verifying-the-signed-payload).
        2. Identify the user (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#identifying-users).
        3. Remove the user’s data from your app’s database.

        https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#uninstall-callback

        Todo: Need to implement this for BigCommerce admin interface.
        """
        LOGGER.info(
            u"Initiated single-click app `uninstall_callback` from BigCommerce"
        )

        # Decode and verify payload
        payload = request.GET.get('signed_payload_jwt')
        try:
            user_data = BigcommerceApi.oauth_verify_payload_jwt(payload, client_secret(), client_id())
            store_hash = user_data['sub'].split('stores/')[1]
        except Exception as e:
            LOGGER.error(
                u"Could not get access token from BigCommerce in `auth_callback`"
            )
            return internal_server_error(e)

        # Lookup store
        store = Store.objects.filter(store_hash=store_hash).first()
        if store is None:
            return HttpResponse("Store not found!", status=401)

        # Clean up: delete store associated users. This logic is up to you.
        # You may decide to keep these records around in case the user installs
        # your app again.
        store_admin_users = StoreAdminUser.objects.filter(store__id=store.id)
        for store_admin_user in store_admin_users:
            store_admin_user.delete()      

        return HttpResponse("Deleted", status=204)

    @classmethod
    def remove_user(cls, request):
        """
        BigCommerce sends a GET request to your app’s remove user callback when a store admin revokes a user’s access to the app.

        The steps to handle this callback are as follows:

        1. Verify the signed payload (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#verifying-the-signed-payload).
        2. Identify the user (https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#identifying-users).
        3. Remove the user’s data from your app’s database.

        https://developer.bigcommerce.com/api-docs/apps/guide/callbacks#remove-user-callback

        Todo: Need to implement this for BigCommerce admin interface.
        """
        LOGGER.info(
            u"Initiated single-click app `remove_user_callback` from BigCommerce"
        )

        # Decode and verify payload
        payload = request.GET.get('signed_payload_jwt')
        try:
            user_data = BigcommerceApi.oauth_verify_payload_jwt(payload, client_secret(), client_id())
            bc_store_admin_user_id = user_data['user']['id']
            store_hash = user_data['sub'].split('stores/')[1]
        except Exception as e:
            LOGGER.error(
                u"Could not get access token from BigCommerce in `auth_callback`"
            )
            return internal_server_error(e)

        # Lookup store
        store = Store.objects.filter(store_hash=store_hash).first()
        if store is None:
            return HttpResponse("Store not found!", status=401)

        # Lookup user and delete it
        admin_user = AdminUser.objects.filter(bc_id=bc_store_admin_user_id)
        if admin_user is not None:
            store_admin_user = StoreAdminUser.objects.filter(bc_admin_user__id=bc_store_admin_user_id, store__id=store.id).first()
            store_admin_user.delete()
        
        return HttpResponse("Deleted", status=204)

