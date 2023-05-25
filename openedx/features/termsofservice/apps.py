"""
Announcements Application Configuration
"""


from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs, PluginSettings

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class TermsOfServiceConfig(AppConfig):
    """
    Application Configuration for TermsOfService
    """
    name = 'openedx.features.termsofservice'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: 'termsofservice',
                PluginURLs.REGEX: '^termsofservice/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: 'settings.test'},
            }
        }
    }
