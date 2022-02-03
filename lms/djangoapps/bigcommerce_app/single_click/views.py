import logging
import time

from django.http import HttpResponse
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from common.djangoapps.edxmako.shortcuts import render_to_response

from bigcommerce.api import BigcommerceApi
from lms.djangoapps.bigcommerce_app.models import StoreAdminUser
from lms.djangoapps.bigcommerce_app.utils import client_id

LOGGER = logging.getLogger(__name__)
# _ = translation.ugettext


@xframe_options_exempt
def single_click_index(request):
    """
    Provides the view for the BigCommerce index page. To be used from the callback
    /auth and /load endpoints.
    """
    LOGGER.info(
        u"Call `single_click_index` successfully."
    )

    # Lookup store
    # Todo: This doesn't work at the moment.
    # store_admin_user_id = request.COOKIES.get("bc_storeadminuserid", None)
    store_admin_user_id = request.GET.get('bc_storeadminuserid', None)
    if not store_admin_user_id:
        return HttpResponse("Not logged in!", status=401)

    store_admin_user = StoreAdminUser.objects.filter(bc_admin_user__bc_id=store_admin_user_id).first()
    if store_admin_user is None:
        return HttpResponse("Not logged in!", status=401)
    store = store_admin_user.store
    admin_user = store_admin_user.bc_admin_user

    # Construct api client for BigCommerce
    client = BigcommerceApi(client_id=client_id(),
                            store_hash=store.store_hash,
                            access_token=store.access_token)

    # Fetch customers for the store.
    customers = client.Customers.all()

    context = {
        'document_title': _(u'BigCommerce Single-Click App – EducateWorkforce'),
        'admin_user': admin_user,
        'store': store,
        'customers': customers,
        # 'client_id': client_id()
    }

    if request.method == 'GET':
        return render_to_response("bigcommerce_app/index.html", context)

    return HttpResponse("Single Click App", status=301)
