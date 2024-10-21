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

import uuid
from datetime import datetime

DRAFT_DIR = "drafts"
PUBLISHED_DIR = "published"

DEFAULT_CONTENT_FIELDS = ['metadata', 'data']

def create_uuid():
    return 'g' + (str(uuid.uuid4())).replace('-', '')

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

        self.course_settings_identifier = None

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

    def get_sequential_modules(self, modulestore, courselike_key):
        """
        Retrieve all sequential modules from the course.
        """
        with modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, courselike_key):
            # Get all top-level modules (e.g., chapters, sections)
            top_level_modules = modulestore.get_items(courselike_key)

            sequentials = []
            for module in top_level_modules:
                if module.category == 'sequential':
                    sequentials.append(module)
        return sequentials

    def export_assignment_groups(self, modulestore, courselike, export_fs):
        # Create root
        root = lxml.etree.Element(
            'assignmentGroups',
            nsmap = {
                None: 'http://canvas.instructure.com/xsd/cccv1p0',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')
                
        position = 1
        # Accessing each asignment type with their weight
        for grade in courselike.grading_policy['GRADER']:
            grade_name = grade['type']
            grade_weight = grade['weight'] * 100 # openedx uses 0-1 grading weight, imscc uses 0-100
            assignment_group = lxml.etree.SubElement(root, 'assignmentGroup', {'identifier': create_uuid()})
            lxml.etree.SubElement(assignment_group, 'title').text = 'EW - ' + grade_name
            lxml.etree.SubElement(assignment_group, 'position').text = str(position)
            position += 1
            lxml.etree.SubElement(assignment_group, 'group_weight').text = str(grade_weight)

        with export_fs.open('course_settings/assignment_groups.xml', 'wb') as assignment_groups_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(assignment_groups_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_media_tracks(self, export_fs):
        # Create root
        root = lxml.etree.Element(
            'media_tracks',
            nsmap = {
                None: 'http://canvas.instructure.com/xsd/cccv1p0',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')
        
        with export_fs.open('course_settings/media_tracks.xml', 'wb') as media_tracks_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(media_tracks_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_files_meta(self, export_fs):
        # Create root
        root = lxml.etree.Element(
            'fileMeta',
            nsmap = {
                None: 'http://canvas.instructure.com/xsd/cccv1p0',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')
        
        with export_fs.open('course_settings/files_meta.xml', 'wb') as files_meta_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(files_meta_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_course_settings(self, modulestore, courselike_key, export_fs):
        # Create root
        root = lxml.etree.Element(
            'course',
            nsmap = {
                None: 'http://canvas.instructure.com/xsd/cccv1p0',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')

        lxml.etree.SubElement(root, 'title').text = str(courselike_key)
        lxml.etree.SubElement(root, 'course_code').text = str(courselike_key)
        lxml.etree.SubElement(root, 'group_weighting_scheme').text =  "percent"

        # Below are additional settings that can be enabled to be the default for openedx -> canvas
        # or they can be set manually after the creation of the canvas class
        # lxml.etree.SubElement(root, 'is_public').text = false
        # lxml.etree.SubElement(root, 'is_public_to_auth_users').text = false
        # lxml.etree.SubElement(root, 'allow_student_wiki_edits').text = false
        # lxml.etree.SubElement(root, 'allow_student_forum_attachments').text = true
        # lxml.etree.SubElement(root, 'lock_all_announcements').text = false
        # lxml.etree.SubElement(root, 'default_wiki_editing_roles').text = teachers
        # lxml.etree.SubElement(root, 'allow_student_organized_groups').text = true
        # lxml.etree.SubElement(root, 'default_view').text = modules
        # lxml.etree.SubElement(root, 'show_total_grade_as_points').text = false
        # lxml.etree.SubElement(root, 'allow_final_grade_overrides').text = false
        # lxml.etree.SubElement(root, 'open_enrollment').text = false
        # lxml.etree.SubElement(root, 'filter_speed_grader_by_student_group').text = false
        # lxml.etree.SubElement(root, 'self_enrollment').text = false
        # lxml.etree.SubElement(root, 'license').text = private
        # lxml.etree.SubElement(root, 'indexed').text = false
        # lxml.etree.SubElement(root, 'hide_final_grade').text = false
        # lxml.etree.SubElement(root, 'hide_distribution_graphs').text = false
        # lxml.etree.SubElement(root, 'allow_student_discussion_topics').text = true
        # lxml.etree.SubElement(root, 'allow_student_editing').text = true
        # lxml.etree.SubElement(root, 'show_announcements_on_home_page').text = false
        # lxml.etree.SubElement(root, 'home_page_announcement_limit').text = 3
        # lxml.etree.SubElement(root, 'usage_rights_required').text = false
        # lxml.etree.SubElement(root, 'restrict_student_future_view').text = false
        # lxml.etree.SubElement(root, 'restrict_student_past_view').text = true
        # lxml.etree.SubElement(root, 'homeroom_course').text = false
        # lxml.etree.SubElement(root, 'grading_standard_enabled').text = false

        with export_fs.open('course_settings/course_settings.xml', 'wb') as media_tracks_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(media_tracks_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def write_imsmanifest_xml(self, export_fs, modulestore, courselike_key):
        ############### Metadata section of imsmanifeset.xml ####################
        # Create the root element with proper namespaces
        root = lxml.etree.Element(
            'manifest',
            {
                'identifier': create_uuid()
            },
            nsmap={
                None: 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1',  # Default namespace
                'lom': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource',
                'lomimscc': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        # Set the schemaLocation attribute
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd '
                'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd '
                'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lommanifest_v1p0.xsd')

        # Create the metadata element
        metadata = lxml.etree.SubElement(root, 'metadata')
        lxml.etree.SubElement(metadata, 'schema').text = 'IMS Common Cartridge'
        lxml.etree.SubElement(metadata, 'schemaversion').text = '1.1.0'

        # Create the LOM element
        lom = lxml.etree.SubElement(metadata, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}lom')

        # Build the general element
        general = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}general')
        title = lxml.etree.SubElement(general, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}title')
        lxml.etree.SubElement(title, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}string').text = 'TEMP-TITlE' # Need to extract some general title

        # Create the lifecycle element
        lifecycle = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}lifeCycle')
        contribute = lxml.etree.SubElement(lifecycle, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}contribute')
        date = lxml.etree.SubElement(contribute, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}date')
        lxml.etree.SubElement(date, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}dateTime').text = (datetime.now()).strftime('%Y-%m-%d') # extract current date

        # Create the rights element
        rights = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}rights')
        copyright = lxml.etree.SubElement(rights, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}copyrightAndOtherRestrictions')
        lxml.etree.SubElement(copyright, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}value').text = 'yes'
        description = lxml.etree.SubElement(rights, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}description')
        lxml.etree.SubElement(description, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}string').text = 'Private (Copyrighted) - http://en.wikipedia.org/wiki/Copyright'

        ######################## Organizations section of imsmanifest.xml ##########################

        # Create organizations and organization element
        organizations = lxml.etree.SubElement(root, 'organizations')
        organization = lxml.etree.SubElement(organizations, 'organization', {'identifier': 'org_1', 'structure': 'rooted-hierarchy'})

        # Create outer learning_module, for first iteration of imscc_exporter, this will be hard coded for the one course, later implementations will need to incorporate multiple courses
        learning_modules = lxml.etree.SubElement(organization, 'item', {'identifier': 'uuid'})
        module = lxml.etree.SubElement(learning_modules, 'item', {'identifier': 'uuid'})
        lxml.etree.SubElement(module, 'title').text = (self.get_key()).course

        uuids = []

        # Build out all the sequentials underneath the one learning module (course)
        sequential_modules = self.get_sequential_modules(modulestore, courselike_key)
        for sequential in sequential_modules:
            identifier = create_uuid()
            uuids.append(identifier)
            sequential_xml = lxml.etree.SubElement(module, 'item', {'identifier': identifier})
            lxml.etree.SubElement(sequential_xml, 'title').text = str(getattr(sequential, 'display_name'))

        tree = lxml.etree.ElementTree(root)
        tree.write('test2.xml', xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_all_course_settings(self, courselike, modulestore, courselike_key, export_fs):
        export_fs.makedirs('course_settings', recreate=True)
        self.export_assignment_groups(modulestore, courselike, export_fs)
        self.export_media_tracks(export_fs)
        self.export_files_meta(export_fs)
        self.export_course_settings(modulestore, courselike_key, export_fs)

    def export(self):
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

                self.export_all_course_settings(courselike, self.modulestore, self.courselike_key, export_fs)
                
"""
Function "export_course_to_imscc" below get called by the django management comman from export_olx.py
"""

def export_course_to_imscc(modulestore, contentstore, course_key, root_dir, course_dir):
    """
    Thin wrapper for the Export Manager. See ExportManager for details.
    """
    TestExportManager(modulestore, contentstore, course_key, root_dir, course_dir).export()