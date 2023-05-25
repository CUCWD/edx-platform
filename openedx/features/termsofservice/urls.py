from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required
from openedx.features.termsofservice.api.v1.urls import urlpatterns as urls_api
urlpatterns = [
  path('termsofservice/', include('openedx.features.termsofservice.api.v1.urls')),
]
