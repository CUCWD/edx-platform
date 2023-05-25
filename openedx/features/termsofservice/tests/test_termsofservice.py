"""
Unit tests for the announcements feature.
"""


import json
import unittest
import datetime
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from common.djangoapps.student.tests.factories import AdminFactory
from openedx.features.termsofservice.models import TermsOfService, TermsOfServiceSites, TermsOfServiceAllSites
from django.contrib.sites.models import Site


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestGlobalTermsOfService(TestCase):
    """
    Test TermsOfService in LMS
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Fill in sample data for TermsOfService
        tos1 = TermsOfService.objects.create(
            date_modified=datetime.datetime.now(),
            terms_of_service_text="<p>Sample terms of service text 1</p>",
            curf_id="cf_id1"
        )
        # Fill in sample data for Site
        site1 = Site.objects.create(
            domain="example-tos.com",
            name="Example TOS Site"
        )

        # Fill in sample data for TermsOfServiceSites
        toss1 = TermsOfServiceSites.objects.create(
            site=site1,
            curf=tos1
        )

        # Fill in sample data for TermsOfServiceAllSites
        tosas = TermsOfServiceAllSites.objects.create(
            curf=tos1
        )

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.admin = AdminFactory.create(
            email='staff@edx.org',
            username='admin',
            password='pass'
        )
        self.client.login(username=self.admin.username, password='pass')

    def test_feature_flag_disabled(self):
        """Ensures that the default settings effectively disables the feature"""
        response = self.client.get('/dashboard')
        self.assertNotContains(response, '<div id="tos-modal"')

    @patch.dict(settings.FEATURES, {'ENABLE_TERMSOFSERVICE': True})
    def test_feature_flag_enabled(self):
        """Ensures that enabling the flag, enables the feature"""
        response = self.client.get('/dashboard')
        self.assertContains(response, '<div id="tos-modal"')
