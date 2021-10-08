"""
Specific overrides that need to be hidden from a repo. This is also to be used with devstack.
""" 

############## Remote Container Debugging for LMS with VS Code #########################
# https://opencraft.com/blog/tutorial-attaching-visual-studio-code-to-devstack-lms-container/
# https://blog.hipolabs.com/remote-debugging-with-vscode-docker-and-pico-fde11f0e5f1c
# Make sure the LMS enables debugging via ptvsd. 

# import importlib.util
# import os
# import subprocess
# import ptvsd

# ENABLE_DEBUGGER_PARAM = "python"
# def start_ptvsd_debugger():
#     parent_pid = os.getppid()
#     cmd = "ps aux | grep %s | awk '{print $2}'" % ENABLE_DEBUGGER_PARAM
#     ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
#     pids = ps.communicate()[0].split('\n')

#     if str(parent_pid) in pids:
#         print('Starting ptvsd debugger')
#         # https://discuss.openedx.org/t/tutorial-attaching-visual-studio-code-to-devstack-lms-container/458/26?u=zachary_trabookis
#         if os.environ.get('RUN_MAIN') or os.environ.get('WERKZEUG_RUN_MAIN'):
#             ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)

# start_ptvsd_debugger() 

# https://vinta.ws/code/tag/debug/page/2

# try:
#     import socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.close()

#     # Check to see that `ptvsd` gets installed.
#     app_name = 'ptvsd'
#     if importlib.util.find_spec(app_name) is None:
#         try:
#             __import__(app_name)
#         except ImportError:
#             print('could not import ptvsd')

#     import ptvsd
#     # ptvsd.enable_attach('my_secret', address=('0.0.0.0', 3000))
#     # https://discuss.openedx.org/t/tutorial-attaching-visual-studio-code-to-devstack-lms-container/458/26?u=zachary_trabookis
#     if os.environ.get('RUN_MAIN') or os.environ.get('WERKZEUG_RUN_MAIN'):
#         ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
#         print('ptvsd is started')
#         ptvsd.wait_for_attach()
#         print('debugger is attached')
# except OSError as exc:
#     print(exc)   

# ===========================================
# Read from /edx/etc/{lms,studio}.yml files for new configuration
# Slack: https://openedx.slack.com/archives/C08B4LZEZ/p1599156714012200

# import codecs
# import copy
# import yaml
# from django.core.exceptions import ImproperlyConfigured

# def get_env_setting(setting):
#     """ Get the environment setting or return exception """
#     try:
#         return os.environ[setting]
#     except KeyError:
#         error_msg = u"Set the %s env variable" % setting
#         raise ImproperlyConfigured(error_msg)

# # A file path to a YAML file from which to load all the configuration for the edx platform
# CONFIG_FILE = get_env_setting('LMS_CFG')

# with codecs.open(CONFIG_FILE, encoding='utf-8') as f:
#     __config__ = yaml.safe_load(f)

#     # ENV_TOKENS and AUTH_TOKENS are included for reverse compatibility.
#     # Removing them may break plugins that rely on them.
#     ENV_TOKENS = __config__
#     AUTH_TOKENS = __config__

#     # Add the key/values from config into the global namespace of this module.
#     # But don't override the FEATURES dict because we do that in an additive way.
#     __config_copy__ = copy.deepcopy(__config__)

#     KEYS_WITH_MERGED_VALUES = [
#         'FEATURES',
#         'TRACKING_BACKENDS',
#         'EVENT_TRACKING_BACKENDS',
#         'JWT_AUTH',
#         'CELERY_QUEUES',
#         'MKTG_URL_LINK_MAP',
#         'MKTG_URL_OVERRIDES',
#     ]
#     for key in KEYS_WITH_MERGED_VALUES:
#         if key in __config_copy__:
#             del __config_copy__[key]

#     vars().update(__config_copy__)      

from .common import FEATURES, JWT_AUTH, INSTALLED_APPS, AUTHENTICATION_BACKENDS, TEMPLATES, PROJECT_ROOT

PLATFORM_NAME = 'EducateWorkforce'

HTTPS = 'off'
LMS_BASE = 'localhost:18000' # 'ztraboo2.ddns.net:18000'  # 'courses.edx.devstack:18000'
CMS_BASE = 'localhost:18010' # 'ztraboo2.ddns.net:18010'  # 'edx.devstack.studio:18010'
SITE_NAME = LMS_BASE
LMS_ROOT_URL = 'http://{}'.format(LMS_BASE)
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL

SESSION_COOKIE_DOMAIN = None
# SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

TECH_SUPPORT_EMAIL = 'support@educateworkforce.com'

################################ FEATURES ################################

FEATURES.update({
    'PREVIEW_LMS_BASE': 'preview.{}'.format(LMS_BASE),
    'ENABLE_SYSADMIN_DASHBOARD': True
})

################################ FORMS ################################

# Configure the custom registration form by installing this repo in the virtual environment
# for this application then use the following configuration to use it within the LMS app.
# Download this to the DEVSTACK_WORKSPACE/edx-platform/src directory before installing it on the LMS container.
# https://github.com/CUCWD/custom-form-app
#
# Install with `pip install -e .` within the LMS container at /edx/src/custom-form-app/.
# Run database migrations `make lms-update-db` within the host DEVSTACK_WORKSPACE/devstack.

ADDL_INSTALLED_APPS = [
    'custom_reg_form'
]
for app in ADDL_INSTALLED_APPS:
    INSTALLED_APPS.append(app)

REGISTRATION_EXTENSION_FORM = 'custom_reg_form.forms.ExtraInfoForm'

################################ SUPPORT ################################

FEATURES.update({
    'ENABLE_FEEDBACK_SUBMISSION': True,
})

if FEATURES.get('ENABLE_FEEDBACK_SUBMISSION'):
    CONTACT_FORM_SUBMISSION_BACKEND = 'support_ticket'  # 'email'

    # This is set in the ./lms.env.json in production
    FEEDBACK_SUBMISSION_EMAIL = 'support@educateworkforce.zendesk.com'  #'support@educateworkforce.com'

    ##### Zendesk #####
    ZENDESK_URL = 'https://educateworkforce.zendesk.com/'
    ZENDESK_USER = 'sc.workforce.development@gmail.com'
    ZENDESK_API_KEY = '93HTZDIlzmyBW9AEfJlyK6Nu2xS79CjnDea6FEsu'
    ZENDESK_CUSTOM_FIELDS = {
        "type_detail": 360038307393,
        "application": 360038321953,
        "course_id": 360038323113,
        "enrollment_mode": 360038352974,
        "enterprise_customer_name": 360038323153
    }

########################## Third Party Auth #######################

# This is overriden within the Site Configuration
FEATURES.update({
    'ENABLE_COMBINED_LOGIN_REGISTRATION': True,
    'ENABLE_THIRD_PARTY_AUTH': True
})

if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = 'MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDGNrcMtMKYhYCt JGuw5JwS04nkJDua9lYX0fSwk33AXaX/InJUQP0tXRcZwqMF4BQ6gVtL7rD1j0XI tXz3g6vMc3fvgvHn/n/oXimYUPYSZA3pxKwa+jKcaQGpzAKLvyi8ccxhscFSCLiW AFpJJZIezHpeB7l5ov3rw0SJwKW8SQRSf8KrqoEjBvHhRUFM+8+kyR4OrhliB7Ka SEhiBycuuDJ/gw4A5OD/TVSTG2BC04sJUpxnnbc+0Wb1d6aqOgMLC5FuXAX6gi/W 7LH7X15p5pDMlc//1Cf07obeAGLr+5vaQLZRC3AVYduCWwMaPVyK1ffScCHUg1Xr CMQDBeJFAgMBAAECggEAcrSbPekla+pmSsx23cmOYH62n6YwMD86F1LTTZQtA7Ou KnWewA9T9HqYsbmnafEBA9J0KP8avSCKe9o7VWmHdCumTp7yqxTmpGxJmfHQVVg9 jPjZuEruGwHRipebKZAYXOVmJ2scuwJ8/6F4njf11Yjzj5LczP18AIHiGe24e7qn IrNh/8tTc50rRFdFbZsFHEdMsn5mjV3IYl8O0WJ/KoUnlQYOnvH6H2IKTZsUvbnN YGZhB5eL84CwknRMALG5bq+ju7iVT5ar6GIjj2x/Std+dXNjm9AXUoPGn3V/Tn8g 1cyXGqnGhQnLEx+NsVMGEQTenlLuE872GTbXjnziQQKBgQD88L14M3ObHesv0HFF lb7TdzSog+PtJ7H3vnMiUavTbHpIl6CjW94RlcLRKKHUZiwktahSoRMGQRD651LE TzH4p+8WDAhUpa4HCSjb5/IAFRDJVtbs6e07RX82E4o8lRbKd3hmVsP8gcAeeLx8 FJ26/GraDlLIJNUZBSTgSeQGfQKBgQDInIHgt2KoMn28JH5vfFJBlg2urOkG0i4p xgHFhci9odb5x9MOVqsxMmf0nZcAPWCnBG98dGP5/fMnjHUciKZQO7YKlSb117KW nnJ/0GLOgdM+8RwEJwIv1H+TTAGnQC8V9aAk1jb5OI8RNCdG0tvby3/eQQ9ZILV5 eKDpNWxtaQKBgQD6s65H/k8+VtguCx7KRpLeTA/AWwFFpQuLL5Q0VtjE9Ib7fnY0 lDC2I0b2Qpyrxh1IwVi1lXsivskStsbdVlWETQb3RjPXmmO0C4sY83t0Q2zg8paS OYXuMoLU2WcxhuARC3sljCgzFXOTgD3pihGQLPHHcVzxjTg91VBokjRVjQKBgQCf /1sCi6BOv35SiNSiPAgqsO+WqedsfkM9I+QT0kCpJaOcMYgd/neo1CffC7T8BvfI HRyBqR53qte8aiSZLk9e3FCzHgQlvPN9dz+guuWjCB4gLBKJKUdwOE3Lf6ot513m aLFhz8umdzp7oRnWPaQGJ8aCz2bbUeAK0m+br/UbSQKBgENmohdJetDkKuJTih1J nVtrZFYIDhztQEh1YLJ1WNMdUDqOjNRMuMpQXG73fIA6GduOLqggFh7qsHuHGg51 ztOI/xzV/j8PLk7vZGJ86NauuZVjg4rjvP4vCi8Ji4DA7EFYqSljqybeVdSrtnpC hT3gC4SBEjiKCf7apEAn+xTJ'
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = 'MIIDLDCCAhSgAwIBAgIJAOu/OQx4cw5sMA0GCSqGSIb3DQEBBQUAMB8xHTAbBgNV BAMTFGVkdWNhdGV3b3JrZm9yY2UuY29tMB4XDTE0MDcxNDE4NDIwOFoXDTE3MDcx MzE4NDIwOFowHzEdMBsGA1UEAxMUZWR1Y2F0ZXdvcmtmb3JjZS5jb20wggEiMA0G CSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDGNrcMtMKYhYCtJGuw5JwS04nkJDua 9lYX0fSwk33AXaX/InJUQP0tXRcZwqMF4BQ6gVtL7rD1j0XItXz3g6vMc3fvgvHn /n/oXimYUPYSZA3pxKwa+jKcaQGpzAKLvyi8ccxhscFSCLiWAFpJJZIezHpeB7l5 ov3rw0SJwKW8SQRSf8KrqoEjBvHhRUFM+8+kyR4OrhliB7KaSEhiBycuuDJ/gw4A 5OD/TVSTG2BC04sJUpxnnbc+0Wb1d6aqOgMLC5FuXAX6gi/W7LH7X15p5pDMlc// 1Cf07obeAGLr+5vaQLZRC3AVYduCWwMaPVyK1ffScCHUg1XrCMQDBeJFAgMBAAGj azBpMEgGA1UdEQRBMD+CFGVkdWNhdGV3b3JrZm9yY2UuY29thidodHRwczovL2Vk dWNhdGV3b3JrZm9yY2UuY29tL3NoaWJib2xldGgwHQYDVR0OBBYEFEHFrYj4N2We gCygs6dchLzayMsDMA0GCSqGSIb3DQEBBQUAA4IBAQAquJj4PyTydYES7sicBI2k nkgHvUbR2EpCfV19KROIayR/IW1HHA0rhB3+3iOXiGEK1u8f92tI7e2+AidMjJEo hvtSUZaWXZgBj3kWt/BGEHakFFKraJ+0tnQ/caB3nzuP6+f+35tFj2E2COi5KMib TyJdsC7ArUYmG8Fsp4tjx7ho9VISR4RpA1sQgyhNsLbzUELLENaMHbKS73D18qTI 9MuqeWRUZWoRa8ISchinry3/BE1D7BhzL/sF09aJk/jdBGLvXChadhgqcVBj6A3r PccwpdFXZ7pP0ycy+Sd1UaTNPzvCwrgYuJfYyCxY5FIB31XJ2UJrrY2vZdvuESVX'


########################## Certificates #######################

FEATURES.update({
    'CERTIFICATES_HTML_VIEW': True
})

############## ENTERPRISE SERVICE API CLIENT CONFIGURATION ######################
# The LMS communicates with the Enterprise service via the EdxRestApiClient class
# These default settings are utilized by the LMS when interacting with the service,
# and are overridden by the configuration parameter accessors defined in aws.py

ENTERPRISE_API_URL = 'http://{}/enterprise/api/v1'.format(LMS_BASE)

############## OPEN EDX ENTERPRISE SERVICE CONFIGURATION ######################
# The Open edX Enterprise service is currently hosted via the LMS container/process.
# However, for all intents and purposes this service is treated as a standalone IDA.
# These configuration settings are specific to the Enterprise service and you should
# not find references to them within the edx-platform project.
#
# Only used if FEATURES['ENABLE_ENTERPRISE_INTEGRATION'] == True.

ENTERPRISE_ENROLLMENT_API_URL = 'http://{}/api/enrollment/v1/'.format(LMS_BASE)


JOURNALS_API_URL = 'https://journals-{}/api/v1/'.format(LMS_BASE)
JOURNALS_URL_ROOT = 'https://journals-{}'.format(LMS_BASE)


################################ Settings for JWTs ################################

# Dummy secret key for dev/test
SECRET_KEY = 'lms-secret'

# 'ISSUER': 'http://courses.{}/oauth2'.format(LMS_BASE),
DEFAULT_JWT_ISSUER = {
    'ISSUER': 'http://{}/oauth2'.format(LMS_BASE), # 
    'SECRET_KEY': SECRET_KEY,
    'AUDIENCE': 'lms-key',
}

JWT_AUTH.update({
    'JWT_SECRET_KEY': DEFAULT_JWT_ISSUER['SECRET_KEY'],
    'JWT_ISSUER': DEFAULT_JWT_ISSUER['ISSUER'],
    'JWT_AUDIENCE': DEFAULT_JWT_ISSUER['AUDIENCE'],
    'JWT_ISSUERS': [
        DEFAULT_JWT_ISSUER,
    ],
})

JWT_ISSUER = 'http://{}/oauth2'.format(LMS_BASE)


############################ OAUTH2 Provider ###################################

OAUTH_OIDC_ISSUER = 'http://{}/oauth2'.format(LMS_BASE)


############################ Search ###################################

# https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/open-release-hawthorn.master/configuration/edx_search.html

# https://github.com/edx/edx-platform/commit/078974d24a0c219d98e4e2cde939b51f0148ccdb
# This was disabled in devstack_docker since setup of Elasticsearch propertly was a concern.

FEATURES.update({

    # Enables and disables Courseware Search feature (in course searching).
    'ENABLE_COURSEWARE_SEARCH': True,

    # Enables and disables Dashboard Search feature (in enrolled courses searching).
    'ENABLE_DASHBOARD_SEARCH': True,

    # Enables and disables Course Discovery feature (over courses searching and facet filtering).
    'ENABLE_COURSE_DISCOVERY': False,

    # Setting for overriding default filtering facets for Course discovery
    # COURSE_DISCOVERY_FILTERS = ["org", "language", "modes"]

})

# Sets the search engine to use. Use ElasticSearch for the search engine
SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"


############################ Milestones ###################################

FEATURES.update({

    # Milestones application flag
    'MILESTONES_APP': True,

    # Prerequisite courses feature flag
    'ENABLE_PREREQUISITE_COURSES': True,

})

############################ LTI Provider ###################################

FEATURES.update({

    # Enable LTI Provider feature.
    'ENABLE_LTI_PROVIDER': True,

})

if FEATURES.get('ENABLE_LTI_PROVIDER'):
    INSTALLED_APPS.append('lti_provider.apps.LtiProviderConfig')
    AUTHENTICATION_BACKENDS.append('lti_provider.users.LtiBackend')


############################ Timed Exams ###################################

FEATURES.update({

    # Special Exams, aka Timed and Proctored Exams
    'ENABLE_SPECIAL_EXAMS': True,

})

######################## GOOGLE ANALYTICS ###########################
GOOGLE_ANALYTICS_ACCOUNT = None
GOOGLE_SITE_VERIFICATION_ID = None
GOOGLE_ANALYTICS_LINKEDIN = 'GOOGLE_ANALYTICS_LINKEDIN_DUMMY'


############## Settings for Badges Frontend #########################
# Setup for badges-frontend
LEARNING_MICROFRONTEND_URL = 'http://localhost:2000'
LMS_FRONTEND_BADGES_CONTAINER_URL = LEARNING_MICROFRONTEND_URL # 'http://localhost:8080' # 'http://localhost:1991' #'http://educateworkforce-mfe-badges.s3-website-us-east-1.amazonaws.com'

0
FEATURES.update({

    # Enable Open Badges feature.
    'ENABLE_OPENBADGES': True,

})

#################### OpenBadges Settings #######################

# Be sure to set up images for course modes using the BadgeImageConfiguration model in the certificates app.
BADGR_API_VERSION = "v2"
BADGR_API_TOKEN_EXPIRATION = 86400
BADGR_API_TOKEN = "FymTGk7wQ3hR268JwS00ngkefdA0GR" # "0WVtn1RWangTSBqf5DDNvEdMTCvSL0"
BADGR_API_REFRESH_TOKEN = "F0HDDPNHK1ZBnSVXpMYHslRiD6Qdir" # Ur7ZWamo8pwaPkK3dim124ak7c1YPG"
# Do not add the trailing slash here.
BADGR_BASE_URL = "https://api.badgr.io"
BADGR_ISSUER_SLUG = "npqlh0acRFG5pKKbnb4SRg"
# Number of seconds to wait on the badging server when contacting it before giving up.
BADGR_TIMEOUT = 10
BADGR_API_NOTIFICATIONS_ENABLED = True
BADGR_PUBLIC_URL = "https://badgr.io"

WRITABLE_GRADEBOOK_URL = 'http://localhost:1994' 

################################ THEMING ################################
# https://github.com/edx/edx-platform/blob/open-release/juniper.master/lms/envs/devstack.py#L388-L405

# from .common import TEMPLATES, PROJECT_ROOT, REPO_ROOT, MAKO_TEMPLATE_DIRS_BASE, LOCALE_PATHS, COMPREHENSIVE_THEME_LOCALE_PATHS, HELP_TOKENS_LANGUAGE_CODE, _make_mako_template_dirs
# from openedx.core.lib.derived import derive_settings

# DEFAULT_SITE_THEME = 'educateworkforce'
# ENABLE_COMPREHENSIVE_THEMING = True

# # COMPREHENSIVE_THEME_DIR = ''
# COMPREHENSIVE_THEME_DIRS = [
#     '/edx/app/edx-themes/edx-platform'
# ]

# TEMPLATES[1]["DIRS"] = _make_mako_template_dirs
# derive_settings(__name__)
 
############## Settings for Qualtrics #########################

QUALTRICS_API_TOKEN = "qPp5jsN6DcsdDIBgDpUcVm5kHblg4Mbdm8ZW8Lzi"
QUALTRICS_API_BASE_URL = "https://clemson.qualtrics.com/API"
QUALTRICS_API_VERSION = "v3"
INSTALLED_APPS.append('qualtricssurvey')