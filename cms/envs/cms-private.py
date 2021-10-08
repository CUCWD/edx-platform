"""
Specific overrides that need to be hidden from a repo. This is also to be used with devstack.
"""

from .common import FEATURES, JWT_AUTH, INSTALLED_APPS

PLATFORM_NAME = 'EducateWorkforce'

HTTPS = 'off'
LMS_BASE = 'localhost:18000' # 'ztraboo.ddns.net:18000'  # 'courses.edx.devstack:18000'
CMS_BASE = 'localhost:18000' # 'ztraboo.ddns.net:18010'  # 'edx.devstack.studio:18010'
SITE_NAME = CMS_BASE
LMS_ROOT_URL = 'http://{}'.format(LMS_BASE)
LMS_INTERNAL_ROOT_URL = LMS_ROOT_URL

FRONTEND_LOGIN_URL = LMS_ROOT_URL + '/login'
FRONTEND_LOGOUT_URL = LMS_ROOT_URL + '/logout'
FRONTEND_REGISTER_URL = LMS_ROOT_URL + '/register'

SESSION_COOKIE_DOMAIN = None  # '.edx.devstack'
# SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

################################ FEATURES ################################

FEATURES.update({
    'PREVIEW_LMS_BASE': 'preview.{}'.format(LMS_BASE)
}) 

################################ THEMING ################################

# ENABLE_COMPREHENSIVE_THEMING = True
# # COMPREHENSIVE_THEME_DIR = ''
# COMPREHENSIVE_THEME_DIRS = [
#     '/edx/app/edx-themes/edx-platform'
# ]


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
    'ISSUER': 'http://{}/oauth2'.format(LMS_BASE),
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

    # Enables and disables courseware content and course info indexing.
    'ENABLE_COURSEWARE_INDEX': True,

    # Enables and disables library content indexing.
    'ENABLE_LIBRARY_INDEX': True

})

if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX']:
    # Sets the search engine to use. Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

    ELASTIC_FIELD_MAPPINGS = {
        "start_date": {
            "type": "date"
        }
    }

############################ Milestones ###################################

FEATURES.update({

    # Milestones application flag
    'MILESTONES_APP': True,

    # Prerequisite courses feature flag
    'ENABLE_PREREQUISITE_COURSES': True,

})

############################ Timed Exams ###################################

FEATURES.update({

    # Special Exams, aka Timed and Proctored Exams
    'ENABLE_SPECIAL_EXAMS': True,

})


# STUDIO_FRONTEND_CONTAINER_URL = 'http://localhost:18011'


############## Settings for Badges Frontend #########################

FEATURES.update({

    # Enable Open Badges feature.
    'ENABLE_OPENBADGES': True,

})

############## Settings for Qualtrics #########################

QUALTRICS_API_TOKEN = "qPp5jsN6DcsdDIBgDpUcVm5kHblg4Mbdm8ZW8Lzi"
QUALTRICS_API_BASE_URL = "https://clemson.qualtrics.com/API"
QUALTRICS_API_VERSION = "v3"
INSTALLED_APPS.append('qualtricssurvey')