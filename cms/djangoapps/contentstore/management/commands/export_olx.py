"""
A Django command that exports a course to a tar.gz file.

If <filename> is '-', it pipes the file to stdout.

This is used by Analytics research exports to provide researchers
with course content.

At present, it differs from Studio exports in several ways:

* It does not include static content.
* The top-level directory in the resulting tarball is a "safe"
  (i.e. ascii) version of the course_key, rather than the word "course".
* It only supports the export of courses.  It does not export libraries.
"""


import os
import re
import shutil
import tarfile
from tempfile import mkdtemp, mktemp
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from path import Path as path

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_exporter import export_course_to_xml
from xmodule.modulestore.imscc_exporter import export_course_to_imscc



class Command(BaseCommand):
    """
    Export a course to XML. The output is compressed as a tar.gz file.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument('course_id',  nargs="+") #nargs = "+" allows parsing of unlimited course ids
        parser.add_argument('--output')
        parser.add_argument('--cc-lti', action = 'store_true', help = 'Run the command with Common Cartridge format')

    def handle(self, *args, **options):
        cc_lti = options.get('cc_lti', False)
        course_ids = options['course_id']
        
        # Raise an error only allowing courses to be exported 1 at a time when not using Common Cartridge packaging standards
        if not cc_lti and len(course_ids) > 1:
            raise CommandError("Can only export 1 OpenEdX course at at time in default OpenEdX packaging standards")

        # stores all the different course keys based on the inputted course ids
        course_keys = []
        for course_id in course_ids:
            try:
                course_keys.append(CourseKey.from_string(course_id))
            except InvalidKeyError:
                raise CommandError("Unparsable course_id")  # lint-amnesty, pylint: disable=raise-missing-from
            except IndexError:
                raise CommandError("Insufficient arguments")  # lint-amnesty, pylint: disable=raise-missing-from

        filename = options['output']
        pipe_results = False

        if filename is None:
            filename = mktemp()
            pipe_results = True

        export_course_to_tarfile(course_keys, filename, cc_lti)

        results = self._get_results(filename) if pipe_results else b''

        # results is of type bytes, so we must write the underlying buffer directly.
        self.stdout.buffer.write(results)

    def _get_results(self, filename):
        """
        Load results from file.

        Returns:
            bytes: bytestring of file contents.
        """
        with open(filename, 'rb') as f:
            results = f.read()
            os.remove(filename)
        return results


def export_course_to_tarfile(course_keys, filename, cc_lti):
    """Exports a course into a tar.gz file"""
    tmp_dir = mkdtemp()
    try:
        course_dir = export_course_to_directory(course_keys, tmp_dir, cc_lti)
        compress_directory(course_dir, filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def export_course_to_directory(course_keys, root_dir, cc_lti):
    """Export course into a directory"""
    # attempt to get all the courses based on the course_keys
    store = modulestore()
    courses = []
    for course_key in course_keys:
        course = store.get_course(course_key)
        if course is None:
            raise CommandError("Invalid course_id")
        courses.append(course)

    course_ids = []
    for course in courses:
        course_ids.append(course.id)
    # The safest characters are A-Z, a-z, 0-9, <underscore>, <period> and <hyphen>.
    # We represent the first four with \w.
    # TODO: Once we support courses with unicode characters, we will need to revisit this.
    replacement_char = '-'
    course_dir = replacement_char.join([courses[0].id.org, courses[0].id.course, courses[0].id.run])
    course_dir = re.sub(r'[^\w\.\-]', replacement_char, course_dir)

    if cc_lti:
        if len(courses) > 1:
            course_dir = "MULTI-COURSE-EXPORT"
        export_course_to_imscc(store, None, course_ids, root_dir, course_dir)
    else:
        export_course_to_xml(store, None, course_ids[0], root_dir, course_dir)

    export_dir = path(root_dir) / course_dir
    return export_dir


def compress_directory(directory, filename):
    """Compress a directory into a tar.gz file"""
    mode = 'w:gz'
    name = path(directory).name
    with tarfile.open(filename, mode) as tar_file:
        tar_file.add(directory, arcname=name)
