# lint-amnesty, pylint: disable=missing-module-docstring

from django.contrib import admin
from .models import TermsOfService, TermsOfServiceAcknowledgement, TermsOfServiceSites, TermsOfServiceAllSites
# Register your models here.


class TermsOfServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'curf_id')


class TermsOfServiceAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'curf')


class TermsOfServiceSitesAdmin(admin.ModelAdmin):
    list_display = ('site', 'curf')


admin.site.register(TermsOfService, TermsOfServiceAdmin)
admin.site.register(TermsOfServiceAcknowledgement, TermsOfServiceAcknowledgementAdmin)
admin.site.register(TermsOfServiceSites, TermsOfServiceSitesAdmin)
admin.site.register(TermsOfServiceAllSites)
