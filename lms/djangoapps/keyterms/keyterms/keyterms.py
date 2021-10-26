"""TO-DO: Write a description of what this XBlock is."""

from typing import List
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import String, Scope, List
from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import json

class KeytermsXBlock(XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    includedKeytermsList = List(
        default=[], scope=Scope.content,
        help="A set to hold all keyterms that are selected to be displayed.",
    )

    keytermhtml = String(
        default="", scope=Scope.content,
        help="A string to hold the html code to display the keyterms.",
    )

    lessonsummary = String(
        default="", scope=Scope.content,
        help="A string to hold the html code to display the lesson summary.",
    )

    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        default="Keyterms"
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # Different views
    def student_view(self, context=None):
        """
        The primary view of the KeytermsXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/keyterms.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/textbox.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js('KeytermsXBlock')
        return frag

    def studio_view(self, context=None):
        html = self.resource_string("static/html/keytermsstudio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/keyterms.css"))
        frag.add_css(self.resource_string("static/css/popover.css"))
        frag.add_css(self.resource_string("static/css/multiselect.css"))
        frag.add_javascript(self.resource_string("static/js/src/keyterms.js"))
        frag.initialize_js('KeytermsXBlock')
        return frag

    # TO-DO: Event handlers
    @XBlock.json_handler
    def edit_lesson(self, data, suffix=''):
        """
        An example handler, which increments the data.
        """
        self.lessonsummary = data['lessonsummary']
        return {"lessonsummary": self.lessonsummary}

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def get_included_keyterms(self, data, suffix=''):
        """
        An example handler, 
        """
        return {"includedKeytermsList": self.includedKeytermsList}

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def add_keyterm(self, data, suffix=''):
        """
        An example handler, 
        """
        self.includedKeytermsList.append(data['keyterm'])
        self.updateKeytermHtml(self.includedKeytermsList, data['course_id'])
        return {"keytermhtml": self.keytermhtml}

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def remove_keyterm(self, data, suffix=''):
        """
        An example handler, 
        """
        self.includedKeytermsList.remove(data['keyterm'])
        self.updateKeytermHtml(self.includedKeytermsList, data['course_id'])
        return {"keytermhtml": self.keytermhtml}

    def updateKeytermHtml(self, list, courseid):
        self.keytermhtml = ""
        for keyterm in list:
            listItem = '<li><a class="keytermli" id="{}" href="http://{}:2000/course/course-v1:{}/glossary">{}</a></li>\n'
            listItem = listItem.format(keyterm, "localhost", courseid, keyterm)
            self.keytermhtml += listItem

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("KeytermsXBlock",
             """<keyterms/>
             """),
            ("Multiple KeytermsXBlock",
             """<vertical_demo>
                <keyterms/>
                <keyterms/>
                <keyterms/>
                </vertical_demo>
             """),
        ]
