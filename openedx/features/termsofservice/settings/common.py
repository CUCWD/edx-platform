"""Common settings for Terms of Service"""


def plugin_settings(settings):
    """
    Common settings for Terms of Service
    .. toggle_name: FEATURES['ENABLE_TERMSOFSERVICE']
    .. toggle_implementation: SettingDictToggle
    .. toggle_default: False
    .. toggle_description: This feature can be enabled to handle prompting users to
         agree to the latest terms of service for a given site.
    .. toggle_use_cases: open_edx
    .. toggle_creation_date: 2022-11-01
    """
    settings.FEATURES['ENABLE_TERMSOFSERVICE'] = False

    # lint-amnesty, pylint: disable=pointless-string-statement
    """
    Common settings for Terms of Service
    .. toggle_name: FEATURES['ENABLE_TERMSOFSERVICE_PER_SUBSITE']
    .. toggle_implementation: SettingDictToggle
    .. toggle_default: False
    .. toggle_description: This feature can be enabled to handle prompting users to
         agree to the latest terms of service for a different subsites.
    .. toggle_use_cases: open_edx
    .. toggle_creation_date: 2022-12-01
    """
    settings.FEATURES['ENABLE_TERMSOFSERVICE_PER_SUBSITE'] = False
