"""
Dump the structure of a course as a JSON object.

The resulting JSON object has one entry for each module in the course:

{
  "$module_url": {
    "category": "$module_category",
    "children": [$module_children_urls... ],
    "metadata": {$module_metadata}
  },

  "$module_url": ....
  ...
}

"""


import json
from datetime import datetime
from pytz import UTC
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xblock.fields import Scope

from xmodule.course_module import CourseBlock
from xmodule.seq_module import SectionBlock
from xblock_discussion import DiscussionXBlock
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import compute_inherited_metadata, own_metadata

from lms.djangoapps.instructor_task.tasks_helper.utils import (
    upload_csv_to_report_store
)

FILTER_LIST = ['xml_attributes']
INHERITED_FILTER_LIST = ['children', 'xml_attributes']


class Command(BaseCommand):  # lint-amnesty, pylint: disable=missing-class-docstring
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        # parser.add_argument('course_id',
        #                     help='specifies the course to dump')
        parser.add_argument('--modulestore',
                            default='default',
                            help='name of the modulestore')
        parser.add_argument('--inherited',
                            action='store_true',
                            help='include inherited metadata')
        parser.add_argument('--inherited_defaults',
                            action='store_true',
                            help='include default values of inherited metadata')

    def handle(self, *args, **options):

        # Get the modulestore

        store = modulestore()

        # Get the course data

        header = ["Course ID", "Course Name", "Course Category", "Course Category Name"]
        csv_rows = []
        csv_rows.insert(0, header)

        courses = store.get_courses()
        course_ids = [x.id for x in courses if x.location.run == 'TEMPLATE']

        import pdb;pdb.set_trace()
        for course_id in course_ids:
            # try:
            #     course_key = CourseKey.from_string(options['course_id'])
            # except InvalidKeyError:
            #     raise CommandError("Invalid course_id")  # lint-amnesty, pylint: disable=raise-missing-from

            # course = store.get_course(course_key)
            course = store.get_course(course_id)
            if course is None:
                raise CommandError("Invalid course_id")

            # Precompute inherited metadata at the course level, if needed:

            if options['inherited']:
                compute_inherited_metadata(course)            
            
            dump_module(str(course_id), course.display_name, course, csv_rows, inherited=options['inherited'], defaults=options['inherited_defaults'])
            
            # Convert course data to dictionary and dump it as JSON to stdout
            # info = dump_module(course, csv_rows, inherited=options['inherited'], defaults=options['inherited_defaults'])
            # return json.dumps(info, indent=2, sort_keys=True, default=str)

        # import pdb;pdb.set_trace()
        # Perform the upload
        start_date = datetime.now(UTC)
        upload_csv_to_report_store(csv_rows, 'course_structure_all_courses_results', course_id, start_date, config_name='COURSE_STRUCTURE_DOWNLOAD')

        pass


def dump_module(course_id, course_name, module, csv_rows=None, destination=None, inherited=False, defaults=False):
    """
    Add the module and all its children to the destination dictionary in
    as a flat structure.
    """

    # destination = destination if destination else {}
    destination = destination if destination else []
    row = []

    items = own_metadata(module)

    # # HACK: add discussion ids to list of items to export (AN-6696)
    # if isinstance(module, DiscussionXBlock) and 'discussion_id' not in items:
    #     items['discussion_id'] = module.discussion_id

    filtered_metadata = {k: v for k, v in items.items() if k not in FILTER_LIST}

    # destination[str(module.location)] = {
    #     'category': module.location.block_type,
    #     'children': [str(child) for child in getattr(module, 'children', [])],
    #     'metadata': filtered_metadata,
    # }
    # destination[str(module.location)] = filtered_metadata['display_name']
    row.append(course_id)
    row.append(course_name)
    row.append(module.location.block_type)

    if isinstance(module, CourseBlock):
        row.append('')
    else:
        row.append(filtered_metadata['display_name'])    

    # if inherited:
    #     # When calculating inherited metadata, don't include existing
    #     # locally-defined metadata
    #     inherited_metadata_filter_list = list(filtered_metadata.keys())
    #     inherited_metadata_filter_list.extend(INHERITED_FILTER_LIST)

    #     def is_inherited(field):
    #         if field.name in inherited_metadata_filter_list:
    #             return False
    #         elif field.scope != Scope.settings:
    #             return False
    #         elif defaults:
    #             return True
    #         else:
    #             return field.values != field.default

    #     inherited_metadata = {field.name: field.read_json(module) for field in module.fields.values() if is_inherited(field)}  # lint-amnesty, pylint: disable=line-too-long
    #     destination[str(module.location)]['inherited_metadata'] = inherited_metadata

    csv_rows.append(row)

    for child in module.get_children():
        if isinstance(child, SectionBlock):
            dump_module(course_id, course_name, child, csv_rows, destination, inherited, defaults)

    return destination
