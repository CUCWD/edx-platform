"""
Dummy backend, for use in testing.
"""


from lms.djangoapps.badges.backends.base import BadgeBackend
from lms.djangoapps.badges.tests.factories import BadgeAssertionFactory, BadgeIssuerFactory


class DummyBackend(BadgeBackend):
    """
    Dummy backend that creates assertions without contacting any real-world backend.
    """
    def award(self, badge_class, user, evidence_url=None):
        return BadgeAssertionFactory(badge_class=badge_class, user=user)

    def get_issuer(self, badge_assertion):
        return BadgeIssuerFactory(badge_assertion=badge_assertion)
