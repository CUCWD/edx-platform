# pylint: disable=E1101
"""
This file exposes an international postcode validator.

Sources: 
http://codeinthehole.com/tips/validating-international-postcodes-in-django/
https://pypi.python.org/pypi/django-localflavor
http://django-localflavor.readthedocs.io/en/latest/localflavor/us/
"""
from __future__ import division

def validate_postcode(country_code):
    """
    Validator that uses localflavor to determine zip code validity.
    """
    # Django 1.3 uses 'UK' instead of GB - this changes in 1.4
    # http://css.dzone.com/articles/using-django-validate
    # https://docs.djangoproject.com/en/1.3/ref/contrib/localflavor/
    # if country_code == 'GB':
    #     country_code = 'UK'
    # module_path = 'django.contrib.localflavor.%s' % country_code.lower()
    module_path = 'localflavor.%s.forms.' % country_code.lower()
    try:
        module = __import__(module_path, fromlist=['forms'])
    except ImportError:
        # No forms module for this country
        return lambda x: x

    fieldname_variants = ['%sPostcodeField',
                          '%sPostCodeField',
                          '%sPostalCodeField',
                          '%sZipCodeField',]
    for variant in fieldname_variants:
        fieldname = variant % country_code.upper()
        if hasattr(module, fieldname):
            return getattr(module, fieldname)().clean
    return lambda x: x