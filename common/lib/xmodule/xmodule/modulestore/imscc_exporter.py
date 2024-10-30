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
import re

DRAFT_DIR = "drafts"
PUBLISHED_DIR = "published"

DEFAULT_CONTENT_FIELDS = ['metadata', 'data']

# Returns an essentially 'unique' uuid for identifying and linking data up
def create_uuid():
    """
    Returns an essentially unique identifier following canvas's default format
    """
    return 'g' + (str(uuid.uuid4())).replace('-', '')

########## THIS FUNCTION DOESN'T WORK ######################################
########## ALL IT DOES IS RETURNS ZERO, NEED TO FIX TO GET ACTUAL SCORE ####
def get_total_score(sequential):
    total_score = 0.0
    
    # Get the direct children of the sequential
    children = sequential.get_children()
    
    for child in children:
        try:
            # Call get_max_score() on the individual child
            score = child.get_max_score()  # Change this line to use child
            total_score += score
        except Exception as e:
            pass  # Handle the exception if necessary
            
        # Recursively get the score from the child's children
        total_score += get_total_score(child)
    
    if total_score != 0:
        print(total_score)
    return total_score

class TestExportManager:
    """
    Manages IMSCC exporting for courselike objects.
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

        """
        Sets up some information to share between export functions

        'sequential_to_identifier': A dictionary mapping each sequential to an unique identifier
                                    An 'identifier' attribute of the 'item' element containing sequential information in the 'imsmanifest.xml' file
                                    An 'identifier' attribute of the 'item' element containing sequential information in the 'course_settings/module_meta.xml' file 
                                    Links sequentials with all the information above

        'sequential_to_identifierref': A dictionary mapping each sequential to an unique identifier
                                       An 'identifierref' attribute of the 'item' element containing sequential information in the 'imsmanifest.xml file'
                                       An 'identifierref' attribute of the 'item' element containing sequential information in the 'course_settings/module_meta.xml' file
                                       An 'identifier' attribute of the assignment object in each sequential's individual assignment_settings.xml file
                                       The name of the folder that stores a sequential's assignment_settings.xml file and html file
                                       Links sequentials with all the information above
        
        'chapter_to_identifier': A dictionary mapping each chapter to an unique identifier
                                 An 'identifier' attribute of the 'item' element containing chapter information in the 'imsmanifest.xml' file
                                 An 'identifier' attribute of the 'item' element containing chapter information in the 'course_settings/module_meta.xml' file 
                                 Links sequentials with all the information above
        
        'assignment_group_to_identifier': A dictionary mapping the names of each assignment group to an unique identifier
                                          An 'identifier' attribute of the 'assignmentGroup' element in 'assignment_groups.xml'
                                          An 'assignment_group_identifierref' child element of the 'assignment' element in an assignment's 'assignment_settings.xml' file
                                          Links assignments to their assignment types

        'external_tool_identifierref': A pre-made identifier to link all external tool references
                                       The name of the file + '.xml' in the root directory containing LTI metadata and information
                                       An 'identifierref' attrubute of the 'item' element containing LTI data
                                       An 'external_tool_identifierref' element of the 'assignment' element in an assignment's 'assignment_settings.xml' file

        'course_settings_identifier': A pre-made identifier to link course_settings references
                                       An 'identifier' attrubute of the 'course' element in 'course_settings/course_settings.xml' file containing course settings
                                       An 'identifier' attribute of the 'resource' element in 'imsmanifest.xml' file containing course settings information      

        'module_identifier': A pre-made identifier to link the only module that is created
                             An 'identifier' attribute of the 'item' element under the 'item' element with the identifier 'LearningModules' in 'imsmanfiest.xml'
                             An 'identifier' attribute of the 'module' element in the 'course_settings/module_meta.xml' file
        """
        
        self.sequential_to_identifier = {}
        self.sequential_to_identifierref = {}
        self.chapter_to_identifier = {}
        self.assignment_group_to_identifier = {}
        self.external_tool_identifierref = create_uuid()
        self.course_settings_identifier = create_uuid()
        self.module_identifier = create_uuid()

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
        Retrieve all sequential modules from the course
        """
        with modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, courselike_key):
            # Get all top-level modules (e.g., chapters, sequentials)
            top_level_modules = modulestore.get_items(courselike_key)

            sequentials = []
            for module in top_level_modules:
                if module.category == 'sequential':
                    sequentials.append(module)
        return sequentials
    
    def get_chapter_modules(self, modulestore, courselike_key):
        """
        Retrieve all chapter modules from the course
        """
        with modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, courselike_key):
            # Get all top-level modules (e.g., chapters, sequentials)
            top_level_modules = modulestore.get_items(courselike_key)

            chapter = []
            for module in top_level_modules:
                if module.category == 'chapter':
                    chapter.append(module)
        return chapter
    
    def get_chapter_sequential_modules(self, modulestore, courselike_key):
        """
        Retrieve all chapter and sequential modules from the course
        """
        with modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, courselike_key):
            # Get all top-level modules (e.g., chapters, sequentials)
            top_level_modules = modulestore.get_items(courselike_key)

            sequentials_chapters = []
            for module in top_level_modules:
                if module.category == 'sequential' or module.category == 'chapter':
                    sequentials_chapters.append(module)
        return sequentials_chapters

    def export_assignment_groups(self, modulestore, courselike, export_fs):
        """
        Exports the 'assignment_groups.xml' file in course_settings
        """
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
        
        # Accessing each asignment type with their weight and adding it to the xml
        for grade in courselike.grading_policy['GRADER']:
            grade_name = grade['type']
            grade_weight = grade['weight'] * 100 # openedx uses 0-1 grading weight, imscc uses 0-100
            self.assignment_group_to_identifier[grade_name] = create_uuid()
            assignment_group = lxml.etree.SubElement(root, 'assignmentGroup', {'identifier': str(self.assignment_group_to_identifier[grade_name])})
            lxml.etree.SubElement(assignment_group, 'title').text = 'EW - ' + grade_name
            lxml.etree.SubElement(assignment_group, 'group_weight').text = str(grade_weight)

        # Write to file
        with export_fs.open('course_settings/assignment_groups.xml', 'wb') as assignment_groups_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(assignment_groups_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_media_tracks(self, export_fs):
        """
        Exports the mostly empty 'media_tracks.xml' file in course_settings
        """

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
        
        # Write to file
        with export_fs.open('course_settings/media_tracks.xml', 'wb') as media_tracks_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(media_tracks_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_files_meta(self, export_fs):
        """
        Exports the mostly empty 'files_meta.xml' file in course_settings
        """
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
        
        # Write to file
        with export_fs.open('course_settings/files_meta.xml', 'wb') as files_meta_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(files_meta_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_course_settings(self, modulestore, courselike_key, export_fs):
        """
        Exports the 'course_settings.xml' file in course_settings
        """
        # Create root
        root = lxml.etree.Element(
            'course',
            {
                'identifier': self.course_settings_identifier
            },
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

        # Write to file
        with export_fs.open('course_settings/course_settings.xml', 'wb') as media_tracks_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(media_tracks_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)
        
        # There's this file called canvas_export.txt that contains nothing but a pun...
        # It's referenced in the ims_manifest file for some reason so we're adding it
        with export_fs.open('course_settings/canvas_export.txt', 'w') as canvas_export_txt:
            canvas_export_txt.write('Q: What did the panda say when he was forced out of his natural habitat?\nA: This is un-BEAR-able\n')

    def export_assignment_folders(self, modulestore, courselike_key, courselike, export_fs):
        """
        Exports all the individual folders for each sequential that is an assignment
        """
        sequential_modules = self.get_sequential_modules(modulestore, courselike_key)
        
        # Parse out non assignments
        assignment_types = {assignment_type['type'] for assignment_type in courselike.grading_policy['GRADER']}
        print(assignment_types)
        only_assignments = (sequential for sequential in sequential_modules if sequential.format in assignment_types)
        
        # Set all the identifiers
        for sequential in sequential_modules:
            self.sequential_to_identifier[sequential] = create_uuid()
            self.sequential_to_identifierref[sequential] = create_uuid()

        for sequential in only_assignments:
            # Create root
            root = lxml.etree.Element(
                'assignment',
                {
                    'identifier': self.sequential_to_identifierref[sequential]
                },
                nsmap={
                    None: 'http://canvas.instructure.com/xsd/cccv1p0',
                    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                }
            )
            root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')
            
            # Add assignment data like points, assignment type, lti, etc.
            lxml.etree.SubElement(root, 'title').text = sequential.display_name
            lxml.etree.SubElement(root, 'assignment_group_identifierref').text = str(self.assignment_group_to_identifier[sequential.format])

            ###### NEED TO FIX #######
            lxml.etree.SubElement(root, 'points_possible').text = str(get_total_score(sequential))
            ##########################

            lxml.etree.SubElement(root, 'submission_types').text = 'external_tool'
            lxml.etree.SubElement(root, 'external_tool_identifierref').text = self.external_tool_identifierref
            lti_link = 'https://courses.educateworkforce.com/lti_provider/courses/' + str(courselike_key) + "/" + (str(courselike_key)).replace('course', 'block') + '+type@sequential+block@' + sequential.url_name
            lxml.etree.SubElement(root, 'external_tool_url').text = lti_link
            lxml.etree.SubElement(root, 'external_tool_data_json').text = '\"\"'
            lxml.etree.SubElement(root, 'external_tool_link_settings_json').text = '{\"selection_width\":\"\",\"selection_height":\"\"}'
            lxml.etree.SubElement(root, 'external_tool_new_tab').text = 'false'
            
            # Create corresponding HTML file
            # HTML files follow this same cookie cutter format with the only thing changing is the title
            html_content ='''<html>
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <title>Assignment: '''

            html_content_pt2 ='''</title>
            </head>
            <body>

            </body>
            </html>'''

            # Make the name of the file match conventions with all lower cases and no spaces, and dashes replacing spaces
            html_file_name = re.sub(r'[^a-zA-Z0-9\s-]', '', sequential.display_name)
            html_file_name = html_file_name.lower()
            html_file_name = html_file_name.replace(' ', '-')
            html_file_name = html_file_name + '.html'
            
            # Write to file
            export_fs.makedirs(str(self.sequential_to_identifierref[sequential]), recreate=True)

            with export_fs.open(str(self.sequential_to_identifierref[sequential]) + '/assignment_settings.xml', 'wb') as assignment_settings_xml:
                tree = lxml.etree.ElementTree(root)
                tree.write(assignment_settings_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

            with export_fs.open(str(self.sequential_to_identifierref[sequential]) + '/' + html_file_name, 'w') as html_file:
                html_file.write(html_content)
                html_file.write(sequential.display_name)
                html_file.write(html_content_pt2)

    def write_imsmanifest_xml(self, modulestore, courselike_key, courselike, export_fs):
        """
        Exports the imsmanifest.xml file
        """

        ############### Metadata section of imsmanifeset.xml ####################

        # Create the root element with proper namespaces
        root = lxml.etree.Element(
            'manifest',
            {
                'identifier': create_uuid()
            },
            nsmap={
                None: 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1',
                'lom': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource',
                'lomimscc': 'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd '
                'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd '
                'http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lommanifest_v1p0.xsd')

        # Set all the metadata values
        metadata = lxml.etree.SubElement(root, 'metadata')
        lxml.etree.SubElement(metadata, 'schema').text = 'IMS Common Cartridge'
        lxml.etree.SubElement(metadata, 'schemaversion').text = '1.1.0'

        lom = lxml.etree.SubElement(metadata, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}lom')

        general = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}general')
        title = lxml.etree.SubElement(general, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}title')
        lxml.etree.SubElement(title, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}string').text = str(courselike_key)

        lifecycle = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}lifeCycle')
        contribute = lxml.etree.SubElement(lifecycle, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}contribute')
        date = lxml.etree.SubElement(contribute, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}date')
        lxml.etree.SubElement(date, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}dateTime').text = (datetime.now()).strftime('%Y-%m-%d') # extract current date

        rights = lxml.etree.SubElement(lom, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}rights')
        copyright = lxml.etree.SubElement(rights, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}copyrightAndOtherRestrictions')
        lxml.etree.SubElement(copyright, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}value').text = 'yes'
        description = lxml.etree.SubElement(rights, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}description')
        lxml.etree.SubElement(description, '{http://ltsc.ieee.org/xsd/imsccv1p1/LOM/manifest}string').text = 'Private (Copyrighted) - http://en.wikipedia.org/wiki/Copyright'

        ######################## Organizations section of imsmanifest.xml ##########################

        # Create organizations and organization element
        organizations = lxml.etree.SubElement(root, 'organizations')
        organization = lxml.etree.SubElement(organizations, 'organization', {'identifier': 'org_1', 'structure': 'rooted-hierarchy'})

        learning_module = lxml.etree.SubElement(organization, 'item', {'identifier': 'LearningModules'})

        # Single module is created here for the one course, will need to be updated later to incorporate multiple courses
        module = lxml.etree.SubElement(learning_module, 'item', {'identifier': self.module_identifier})
        lxml.etree.SubElement(module, 'title').text = (self.get_key()).course

        # Build out all the chapters and sequentials underneath the one learning module (course)
        chapter_and_sequential_modules = self.get_chapter_sequential_modules(modulestore, courselike_key)
        for chapter_sequential_module in chapter_and_sequential_modules:
            if chapter_sequential_module.category == 'sequential':
                sequential = lxml.etree.SubElement(module, 'item', {'identifier': self.sequential_to_identifier[chapter_sequential_module], 'identifierref': self.sequential_to_identifierref[chapter_sequential_module]})
                lxml.etree.SubElement(sequential, 'title').text = chapter_sequential_module.display_name
            else:
                self.chapter_to_identifier[chapter_sequential_module] = create_uuid()
                chapter = lxml.etree.SubElement(module, 'item', {'identifier': self.chapter_to_identifier[chapter_sequential_module]})
                print(chapter_sequential_module.display_name)
                lxml.etree.SubElement(chapter, 'title').text = chapter_sequential_module.display_name
            
        ############################# Resources section of imsmanifest.xml #############################
        
        # Create resources element
        resources = lxml.etree.SubElement(root, 'resources')
        type_string = 'associatedcontent/imscc_xmlv1p1/learning-application-resource'
        
        # Course settings
        course_settings_resource = lxml.etree.SubElement(resources, 'resource', {'identifier': self.course_settings_identifier, 'type': type_string, 'href': 'course_settings/canvas_export.txt'})
        course_settings_path = 'course_settings'
        for filename in export_fs.listdir(course_settings_path):
            lxml.etree.SubElement(course_settings_resource, 'file', {'href': 'course_settings/' + filename})

        # Create resources for assignment sequentials
        sequential_modules = self.get_sequential_modules(modulestore, courselike_key)
        
        assignment_types = {assignment_type['type'] for assignment_type in courselike.grading_policy['GRADER']}
        for sequential in sequential_modules:
            if sequential.format in assignment_types:
                html_file_path = self.sequential_to_identifierref[sequential]
                xml_file_path = self.sequential_to_identifierref[sequential]
                for filename in export_fs.listdir(self.sequential_to_identifierref[sequential]):
                    if filename.endswith('.html'):
                        html_file_path = html_file_path + '/' + filename
                    if filename.endswith('xml'):
                        xml_file_path = xml_file_path + '/' + filename
                resource = lxml.etree.SubElement(resources , 'resource', {'identifier': self.sequential_to_identifierref[sequential], 'type': type_string, 'href': html_file_path})
                lxml.etree.SubElement(resource, 'file', {'href': html_file_path})
                lxml.etree.SubElement(resource, 'file', {'href': xml_file_path})

        # Additional last resource for the external tool xml
        external_tool_resource = lxml.etree.SubElement(resources, 'resource', {'identifier': self.external_tool_identifierref, 'type': 'imsbasiclti_xmlv1p0'})
        lxml.etree.SubElement(external_tool_resource, 'file', {'href': self.external_tool_identifierref + '.xml'})

        # Write to file
        with export_fs.open('imsmanifest.xml', 'wb') as imsmanifest_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(imsmanifest_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_external_tool(self, export_fs):
        # Create the root element
        root = lxml.etree.Element(
            'cartridge_basiclti_link',
            nsmap={
                None: "http://www.imsglobal.org/xsd/imslticc_v1p0",
                'blti': "http://www.imsglobal.org/xsd/imsbasiclti_v1p0",
                'lticm': "http://www.imsglobal.org/xsd/imslticm_v1p0",
                'lticp': "http://www.imsglobal.org/xsd/imslticp_v1p0",
                'xsi': "http://www.w3.org/2001/XMLSchema-instance"
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                    "http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd"
                    "http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0p1.xsd"
                    "http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd"
                    "http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd")

        # Basic metadata content
        lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}title', nsmap={'blti': "http://www.imsglobal.org/xsd/imsbasiclti_v1p0"}).text = "EducateWorkforce (courses.educateworkforce.com)"
        lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}description').text = ""
        lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}secure_launch_url').text = "https://courses.educateworkforce.com/lti_provider/"
        vendor = lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}vendor')
        lxml.etree.SubElement(vendor, '{http://www.imsglobal.org/xsd/imslticp_v1p0}code').text = "unknown"
        lxml.etree.SubElement(vendor, '{http://www.imsglobal.org/xsd/imslticp_v1p0}name').text = "unknown"
        lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}custom')
        extensions = lxml.etree.SubElement(root, '{http://www.imsglobal.org/xsd/imsbasiclti_v1p0}extensions', platform="canvas.instructure.com")
        lxml.etree.SubElement(extensions, '{http://www.imsglobal.org/xsd/imslticm_v1p0}property', name="privacy_level").text = "public"
        lxml.etree.SubElement(extensions, '{http://www.imsglobal.org/xsd/imslticm_v1p0}property', name="domain").text = "courses.educateworkforce.com"
        lxml.etree.SubElement(extensions, '{http://www.imsglobal.org/xsd/imslticm_v1p0}property', name="lti_version").text = "1.1"

        with export_fs.open(self.external_tool_identifierref + '.xml', 'wb') as external_tool_identifierref_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(external_tool_identifierref_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_module_meta_xml(self, modulestore, courselike_key, courselike, export_fs):
        """
        Exports the module_meta.xml file in course_settings
        """

        # Get all the chapter and sequential modules to appear under the modules page
        chapter_sequential_modules = self.get_chapter_sequential_modules(modulestore, courselike_key)
        # Parse out assignments (assignments are sequentials with a 'format' in the grading policy)
        assignment_types = {assignment_type['type'] for assignment_type in courselike.grading_policy['GRADER']}

        # Create the root element
        root = lxml.etree.Element(
            'modules',
            nsmap = {
                None: 'http://canvas.instructure.com/xsd/cccv1p0',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
        )

        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                'http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd')

        module = lxml.etree.SubElement(root, 'module', {'identifier': self.module_identifier})
        lxml.etree.SubElement(module, 'title').text =  (self.get_key()).course
        lxml.etree.SubElement(module, 'workflow_state').text = 'active'

        items = lxml.etree.SubElement(module, 'items')

        # Iterate through chapter_sequential_modules and assign their type as they would appear in the modules page
        # Example types: Header that just has text, external tool, assignment, etc.
        for chapter_sequential in chapter_sequential_modules:
            if chapter_sequential.format in assignment_types:
                item = lxml.etree.SubElement(items, 'item', {'identifier': self.sequential_to_identifier[chapter_sequential]})
                lxml.etree.SubElement(item, 'content_type').text = 'Assignment'
                lxml.etree.SubElement(item, 'title').text = chapter_sequential.display_name
                lxml.etree.SubElement(item, 'identifierref').text = self.sequential_to_identifierref[chapter_sequential]
            elif chapter_sequential.category == 'sequential':
                item = lxml.etree.SubElement(items, 'item', {'identifier': self.sequential_to_identifierref[chapter_sequential]})
                lxml.etree.SubElement(item, 'content_type').text = 'ContextExternalTool'
                lxml.etree.SubElement(item, 'title').text = chapter_sequential.display_name
                lxml.etree.SubElement(item, 'identifierref').text = self.external_tool_identifierref
                lti_link = 'https://courses.educateworkforce.com/lti_provider/courses/' + str(courselike_key) + "/" + (str(courselike_key)).replace('course', 'block') + '+type@sequential+block@' + chapter_sequential.url_name
                lxml.etree.SubElement(item, 'url').text = lti_link
            else:
                item = lxml.etree.SubElement(items, 'item', {'identifier': self.chapter_to_identifier[chapter_sequential]})   
                lxml.etree.SubElement(item, 'content_type').text = 'ContextModuleSubHeader'
                lxml.etree.SubElement(item, 'title').text = chapter_sequential.display_name    

        # Write to file
        with export_fs.open('course_settings/module_meta.xml', 'wb') as module_meta_xml:
            tree = lxml.etree.ElementTree(root)
            tree.write(module_meta_xml, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    def export_all_course_settings(self, modulestore, courselike_key, courselike, export_fs):
        """
        Function to export all course_settings at once
        """
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

                # Call export functions
                self.export_external_tool(export_fs)
                self.export_all_course_settings(self.modulestore, self.courselike_key, courselike, export_fs)
                self.export_assignment_folders(self.modulestore, self.courselike_key, courselike, export_fs)
                self.write_imsmanifest_xml(self.modulestore, self.courselike_key, courselike, export_fs)
                self.export_module_meta_xml(self.modulestore, self.courselike_key, courselike, export_fs)
                
"""
Function "export_course_to_imscc" below get called by the django management comman from export_olx.py
"""

def export_course_to_imscc(modulestore, contentstore, course_key, root_dir, course_dir):
    """
    Thin wrapper for the Export Manager. See ExportManager for details.
    """
    TestExportManager(modulestore, contentstore, course_key, root_dir, course_dir).export()