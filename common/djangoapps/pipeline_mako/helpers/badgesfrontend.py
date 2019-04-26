"""
Contains code that gets run inside our mako template
Debugging python-in-mako is terrible, so we've moved the actual code out to its own file
"""
import logging

from django.conf import settings
from django.utils.translation import to_locale

log = logging.getLogger(__name__)


def load_bfe_i18n_messages(language):
    """
    Loads i18n data from badges-frontend's published files.
    """
    messages = "{}"

    try:
        if language != 'en':
            # because en is the default, badges-frontend will have it loaded by default
            messages_path = "{base}/badges-frontend/dist/i18n/messages/{locale}.json".format(
                base=settings.STATIC_ROOT_BASE,
                locale=to_locale(language)
            )
            with open(messages_path) as inputfile:
                messages = inputfile.read()
    except:  # pylint: disable=bare-except
        log.error("Error loading badges-frontend language files", exc_info=True)

    return messages
