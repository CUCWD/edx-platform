"""
Methods for exporting course data to IMSCC
"""


import logging
import os
from abc import abstractmethod
from json import dumps

import lxml.etree
from fs.osfs import OSFS
from opaque_keys.edx.locator import CourseLocator, LibraryLocator
from xblock.fields import Reference, ReferenceList, ReferenceValueDict, Scope

from xmodule.assetstore import AssetMetadata
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from xmodule.modulestore import LIBRARY_ROOT, EdxJSONEncoder, ModuleStoreEnum
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.store_utilities import draft_node_constructor, get_draft_subtree_roots

import lxml.etree
import uuid

DRAFT_DIR = "drafts"
PUBLISHED_DIR = "published"

DEFAULT_CONTENT_FIELDS = ['metadata', 'data']


class TestExportManager:
    """
    Manages XML exporting for courselike objects.
    """
    def __init__(self, modulestore, contentstore, courselike_key, root_dir, target_dir):
        """
        Export all modules from `modulestore` and content from `contentstore` as xml to `root_dir`.

        `modulestore`: A `ModuleStore` object that is the source of the modules to export
        `contentstore`: A `ContentStore` object that is the source of the content to export, can be None
        `courselike_key`: The Locator of the Descriptor to export
        `root_dir`: The directory to write the exported xml to
        `target_dir`: The name of the directory inside `root_dir` to write the content to
        """
        self.modulestore = modulestore
        self.contentstore = contentstore
        self.courselike_key = courselike_key
        self.root_dir = root_dir
        self.target_dir = str(target_dir)

        print(self.modulestore)
        print(self.contentstore)
        print(self.courselike_key)
        print(self.root_dir)
        print(self.target_dir)

    def get_key(self):
        """
        Get the courselike locator key
        """
        return CourseLocator(
            self.courselike_key.org, self.courselike_key.course, self.courselike_key.run, deprecated=True
        )

    def get_courselike(self):
        """
        Get the target courselike object for this export.
        """
        # depth = None: Traverses down the entire course structure.
        # lazy = False: Loads and caches all block definitions during traversal for fast access later
        #               -and- to eliminate many round-trips to read individual definitions.
        # Why these parameters? Because a course export needs to access all the course block information
        # eventually. Accessing it all now at the beginning increases performance of the export.
        return self.modulestore.get_course(self.courselike_key, depth=None, lazy=False)
    
    def get_sequential_modules(self, modulestore, course_key):
        """
        Retrieve all sequential modules from the course.
        """
        with modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
            # Get all top-level modules (e.g., chapters, sections)
            top_level_modules = modulestore.get_items(course_key)

            sequentials = []
            for module in top_level_modules:
                if module.category == 'sequential':
                    sequentials.append(module)
                # Recursively check children if necessary
                if hasattr(module, 'children'):
                    for child in module.children:
                        child_module = modulestore.get_item(child)
                        if child_module.category == 'sequential':
                            sequentials.append(child_module)
        return sequentials

    def get_assignment_xml(self, modulestore, course_key):
        # contains all the default metadata values used in exporting CUCWD's OpenEdX courses to Canvas
        metadata_template = {
        'identifier': '', # custom
        'title': '', # custom
        'due_at': '',
        'lock_at': '',
        'unlock_at': '',
        'module_locked': 'false',
        'assignment_group_identifierref': '', # custom
        'workflow_state': 'published',
        'assignment_overrides': '',
        'allowed_extensions': '',
        'has_group_category': 'false',
        'points_possible': '', # custom
        'grading_type': 'points',
        'all_day': 'false',
        'submission_types': 'external_tool',
        'position': '100',
        'turnitin_enabled': 'false',
        'vericite_enabled': 'false',
        'peer_review_count': '0',
        'peer_reviews': 'false',
        'automatic_peer_reviews': 'false',
        'anonymous_peer_reviews': 'false',
        'grade_group_students_individually': 'false',
        'freeze_on_copy': 'false',
        'omit_from_final_grade': 'false',
        'hide_in_gradebook': 'false',
        'intra_group_peer_reviews': 'false',
        'only_visible_to_overrides': 'false',
        'post_to_sis': 'false',
        'moderated_grading': 'false',
        'grader_count': '0',
        'grader_comments_visible_to_graders': 'true',
        'anonymous_grading': 'false',
        'graders_anonymous_to_graders': 'false',
        'grader_names_visible_to_final_grader': 'true',
        'anonymous_instructor_annotations': 'false',
        'external_tool_identifierref': '', # custom
        'external_tool_url': '', # custom
        'external_tool_data_json': '\"\"',
        'external_tool_link_settings_json': '{\"selection_width\": \"\", "selection_height": \"\"}',
        'external_tool_new_tab': 'false',
        'post_policy': ''
        }

        sequential_modules = self.get_sequential_modules(modulestore, course_key)
        all_sequential_metadata = []
        for sequential in sequential_modules:
            sequential_metadata = metadata_template
            sequential_metadata['title'] = str(getattr(sequential, 'display_name'))
            # will need to build out all identifiers, unsure how they are created or what convention they follow
            # also need to find where the point values are coming from
            # build out the lti link 
            lti_link = 'https://courses.educateworkforce.com/lti_provider/courses/' + str(course_key) + "/" + (str(course_key)).replace('course', 'block') + 'type@' + str(getattr(sequential, 'url_name'))
            print(lti_link)
            sequential_metadata['external_tool_url'] = lti_link
            all_sequential_metadata.append(sequential_metadata)

        print("course_id")
        print(dir(sequential_modules[0]))
        print(sequential_modules[0].scope_ids)
        print(all_sequential_metadata[0])

        

        for sequential_metadata in all_sequential_metadata:
            # 3 types of identifiers that need to be made
            # assignment_group_identifier - links to type of assignment and grading system 
            # identifier - in root, links folder, file, manifest
            # external_tool_identifier - the same across all xml files, helps with usage of lti
            # Generate a UUID following Canvas export standards to create identifiers
            identifier = 'g' + (str(uuid.uuid4())).replace('-', '')

            print(identifier)

            # Create the root element with proper namespaces
            root = lxml.etree.Element(
                'assignment',
                {
                    'identifier': identifier,
                },
                nsmap={
                    None: 'http://canvas.instructure.com/xsd/cccv1p0',  # Default namespace
                    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                }
            )            
            root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', 
                    'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')
            root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', 
            'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')

            for key in sequential_metadata.keys():
                sub_element = lxml.etree.SubElement(root, key)
                if key == 'post_policy':
                    post_sub = lxml.etree.SubElement(sub_element, 'post_manually')
                    post_sub.text = 'false'
                else:
                    sub_element.text = sequential_metadata[key]
                print(key + ': ' + sequential_metadata[key])

            # Convert the t ree to a string
            tree = lxml.etree.ElementTree(root)
            tree.write('test.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export(self):
        
        self.get_assignment_xml(self.modulestore, self.courselike_key)

        """
        Perform the export given the parameters handed to this class at init.
        """
        with self.modulestore.bulk_operations(self.courselike_key):

             fsm = OSFS(self.root_dir)
             root = lxml.etree.Element('unknown')

             # export only the published content
             with self.modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, self.courselike_key):

                 # stores metadata for the course
                 courselike = self.get_courselike()

                 # make the directory to export to
                 export_fs = courselike.runtime.export_fs = fsm.makedir(self.target_dir, recreate=True)
        print("redirected!!!")

"""
Function "export_course_to_imscc" below get called by the django management comman from export_olx.py
"""

def export_course_to_imscc(modulestore, contentstore, course_key, root_dir, course_dir):
    """
    Thin wrapper for the Export Manager. See ExportManager for details.
    """
    TestExportManager(modulestore, contentstore, course_key, root_dir, course_dir).export()