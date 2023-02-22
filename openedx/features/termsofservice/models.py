# pylint: disable=missing-module-docstring

from django.db import models
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.contrib.sites.models import Site
# Create your models here.


class TermsOfService(models.Model):
    """
        Stores the Terms of Service Versions
    """
    class Meta:
        app_label = 'termsofservice'

    # View the object in Django Apps as Curf ID
    def __str__(self):
        return self.curf_id

    date_modified = models.DateTimeField()
    terms_of_service_text = models.TextField()
    curf_id = models.CharField(unique=True, max_length=25)


class TermsOfServiceAcknowledgement(models.Model):
    """
        Model to keep track of a user's agreement to the latest terms and conditions
    """
    class Meta:
        app_label = 'termsofservice'

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    curf = models.ForeignKey(TermsOfService, to_field="curf_id", on_delete=models.CASCADE)


# TermsOfServiceSites
class TermsOfServiceSites(models.Model):
    """
        Model to link a site with its active Terms of Service (Linked via curf_id)
    """
    class Meta:
        app_label = 'termsofservice'
        verbose_name = 'TOS Site'

    site = models.OneToOneField(Site, primary_key=True, on_delete=models.CASCADE)
    curf = models.ForeignKey(TermsOfService, to_field="curf_id", on_delete=models.CASCADE)


# TermsOfServiceAllSites - holds the default site - This model holds only one default object
class TermsOfServiceAllSites(models.Model):
    class Meta:
        app_label = 'termsofservice'
        verbose_name = 'TermsOfServiceAllSite'

    # id = models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)
    curf = models.OneToOneField(TermsOfService, to_field="curf_id", on_delete=models.CASCADE)
    
    # models.ForeignKey(TermsOfService, primary_key=True, to_field="curf_id", on_delete=models.CASCADE)
