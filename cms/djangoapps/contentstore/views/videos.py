"""
Views related to the video upload feature
"""
from datetime import datetime, timedelta
import logging

from boto import s3
import csv
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.translation import ugettext as _, ugettext_noop
from django.views.decorators.http import require_GET, require_POST, require_http_methods
import rfc6266

from edxval.api import (
    create_video,
    get_videos_for_course,
    SortDirection,
    VideoSortField,
    remove_video_for_course,
    update_video_status,
    update_video_image
)
from opaque_keys.edx.keys import CourseKey

from contentstore.models import VideoUploadConfig
from contentstore.utils import reverse_course_url
from edxmako.shortcuts import render_to_response
from util.json_request import expect_json, JsonResponse

from .course import get_course_and_check_access


__all__ = ['videos_handler', 'video_encodings_download', 'video_images_handler']

LOGGER = logging.getLogger(__name__)


# Default expiration, in seconds, of one-time URLs used for uploading videos.
KEY_EXPIRATION_IN_SECONDS = 86400

VIDEO_SUPPORTED_FILE_FORMATS = {
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
}

THUMBNAIL_SUPPORTED_FILE_FORMATS = {
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp'
}

VIDEO_UPLOAD_MAX_FILE_SIZE_GB = 5

# maximum time for video to remain in upload state
MAX_UPLOAD_HOURS = 24


class StatusDisplayStrings(object):
    """
    A class to map status strings as stored in VAL to display strings for the
    video upload page
    """

    # Translators: This is the status of an active video upload
    _UPLOADING = ugettext_noop("Uploading")
    # Translators: This is the status for a video that the servers are currently processing
    _IN_PROGRESS = ugettext_noop("In Progress")
    # Translators: This is the status for a video that the servers have successfully processed
    _COMPLETE = ugettext_noop("Ready")
    # Translators: This is the status for a video that is uploaded completely
    _UPLOAD_COMPLETED = ugettext_noop("Uploaded")
    # Translators: This is the status for a video that the servers have failed to process
    _FAILED = ugettext_noop("Failed")
    # Translators: This is the status for a video that is cancelled during upload by user
    _CANCELLED = ugettext_noop("Cancelled")
    # Translators: This is the status for a video which has failed
    # due to being flagged as a duplicate by an external or internal CMS
    _DUPLICATE = ugettext_noop("Failed Duplicate")
    # Translators: This is the status for a video which has duplicate token for youtube
    _YOUTUBE_DUPLICATE = ugettext_noop("YouTube Duplicate")
    # Translators: This is the status for a video for which an invalid
    # processing token was provided in the course settings
    _INVALID_TOKEN = ugettext_noop("Invalid Token")
    # Translators: This is the status for a video that was included in a course import
    _IMPORTED = ugettext_noop("Imported")
    # Translators: This is the status for a video that is in an unknown state
    _UNKNOWN = ugettext_noop("Unknown")

    _STATUS_MAP = {
        "upload": _UPLOADING,
        "ingest": _IN_PROGRESS,
        "transcode_queue": _IN_PROGRESS,
        "transcode_active": _IN_PROGRESS,
        "file_delivered": _COMPLETE,
        "file_complete": _COMPLETE,
        "upload_completed": _UPLOAD_COMPLETED,
        "file_corrupt": _FAILED,
        "pipeline_error": _FAILED,
        "upload_failed": _FAILED,
        "s3_upload_failed": _FAILED,
        "upload_cancelled": _CANCELLED,
        "duplicate": _DUPLICATE,
        "youtube_duplicate": _YOUTUBE_DUPLICATE,
        "invalid_token": _INVALID_TOKEN,
        "imported": _IMPORTED,
    }

    @staticmethod
    def get(val_status):
        """Map a VAL status string to a localized display string"""
        return _(StatusDisplayStrings._STATUS_MAP.get(val_status, StatusDisplayStrings._UNKNOWN))    # pylint: disable=translation-of-non-string


@expect_json
@login_required
@require_http_methods(("GET", "POST", "DELETE"))
def videos_handler(request, course_key_string, edx_video_id=None):
    """
    The restful handler for video uploads.

    GET
        html: return an HTML page to display previous video uploads and allow
            new ones
        json: return json representing the videos that have been uploaded and
            their statuses
    POST
        json: create a new video upload; the actual files should not be provided
            to this endpoint but rather PUT to the respective upload_url values
            contained in the response
    DELETE
        soft deletes a video for particular course
    """
    course = _get_and_validate_course(course_key_string, request.user)

    if not course:
        return HttpResponseNotFound()

    if request.method == "GET":
        if "application/json" in request.META.get("HTTP_ACCEPT", ""):
            return videos_index_json(course)
        else:
            return videos_index_html(course)
    elif request.method == "DELETE":
        remove_video_for_course(course_key_string, edx_video_id)
        return JsonResponse()
    else:
        if is_status_update_request(request.json):
            return send_video_status_update(request.json)

        return videos_post(course, request)


@expect_json
@login_required
@require_POST
def video_images_handler(request, course_key_string, edx_video_id=None):
    # TODO : We need to be sure what data jQuery fileuploader sends.
    image_file = request.FILES['file']
    file_name = request.FILES['file'].name

    # TODO: Image file validation
    # We can use profile_iamges/images.py validate_uploaded_image method and may be need to abstract out some
    # functionality based on our needs.
    image_url = update_video_image(edx_video_id, course_key_string, image_file, file_name)
    LOGGER.info(
        'VIDEOS: Video image updated for edx_video_id [%s]',
        edx_video_id
    )
    return JsonResponse({'image_url' : 'https://i.imgur.com/jlsMLRO.jpg'})


@login_required
@require_GET
def video_encodings_download(request, course_key_string):
    """
    Returns a CSV report containing the encoded video URLs for video uploads
    in the following format:

    Video ID,Name,Status,Profile1 URL,Profile2 URL
    aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa,video.mp4,Complete,http://example.com/prof1.mp4,http://example.com/prof2.mp4
    """
    course = _get_and_validate_course(course_key_string, request.user)

    if not course:
        return HttpResponseNotFound()

    def get_profile_header(profile):
        """Returns the column header string for the given profile's URLs"""
        # Translators: This is the header for a CSV file column
        # containing URLs for video encodings for the named profile
        # (e.g. desktop, mobile high quality, mobile low quality)
        return _("{profile_name} URL").format(profile_name=profile)

    profile_whitelist = VideoUploadConfig.get_profile_whitelist()

    videos = list(_get_videos(course))
    name_col = _("Name")
    duration_col = _("Duration")
    added_col = _("Date Added")
    video_id_col = _("Video ID")
    status_col = _("Status")
    profile_cols = [get_profile_header(profile) for profile in profile_whitelist]

    def make_csv_dict(video):
        """
        Makes a dictionary suitable for writing CSV output. This involves
        extracting the required items from the original video dict and
        converting all keys and values to UTF-8 encoded string objects,
        because the CSV module doesn't play well with unicode objects.
        """
        # Translators: This is listed as the duration for a video that has not
        # yet reached the point in its processing by the servers where its
        # duration is determined.
        duration_val = str(video["duration"]) if video["duration"] > 0 else _("Pending")
        ret = dict(
            [
                (name_col, video["client_video_id"]),
                (duration_col, duration_val),
                (added_col, video["created"].isoformat()),
                (video_id_col, video["edx_video_id"]),
                (status_col, video["status"]),
            ] +
            [
                (get_profile_header(encoded_video["profile"]), encoded_video["url"])
                for encoded_video in video["encoded_videos"]
                if encoded_video["profile"] in profile_whitelist
            ]
        )
        return {
            key.encode("utf-8"): value.encode("utf-8")
            for key, value in ret.items()
        }

    response = HttpResponse(content_type="text/csv")
    # Translators: This is the suggested filename when downloading the URL
    # listing for videos uploaded through Studio
    filename = _("{course}_video_urls").format(course=course.id.course)
    # See https://tools.ietf.org/html/rfc6266#appendix-D
    response["Content-Disposition"] = rfc6266.build_header(
        filename + ".csv",
        filename_compat="video_urls.csv"
    )
    writer = csv.DictWriter(
        response,
        [
            col_name.encode("utf-8")
            for col_name
            in [name_col, duration_col, added_col, video_id_col, status_col] + profile_cols
        ],
        dialect=csv.excel
    )
    writer.writeheader()
    for video in videos:
        writer.writerow(make_csv_dict(video))
    return response


def _get_and_validate_course(course_key_string, user):
    """
    Given a course key, return the course if it exists, the given user has
    access to it, and it is properly configured for video uploads
    """
    course_key = CourseKey.from_string(course_key_string)

    # For now, assume all studio users that have access to the course can upload videos.
    # In the future, we plan to add a new org-level role for video uploaders.
    course = get_course_and_check_access(course_key, user)

    if (
            settings.FEATURES["ENABLE_VIDEO_UPLOAD_PIPELINE"] and
            getattr(settings, "VIDEO_UPLOAD_PIPELINE", None) and
            course and
            course.video_pipeline_configured
    ):
        return course
    else:
        return None


def convert_video_status(video):
    """
    Convert status of a video. Status can be converted to one of the following:

        *   FAILED if video is in `upload` state for more than 24 hours
        *   `YouTube Duplicate` if status is `invalid_token`
        *   user-friendly video status
    """
    now = datetime.now(video['created'].tzinfo)
    if video['status'] == 'upload' and (now - video['created']) > timedelta(hours=MAX_UPLOAD_HOURS):
        new_status = 'upload_failed'
        status = StatusDisplayStrings.get(new_status)
        message = 'Video with id [%s] is still in upload after [%s] hours, setting status to [%s]' % (
            video['edx_video_id'], MAX_UPLOAD_HOURS, new_status
        )
        send_video_status_update([
            {
                'edxVideoId': video['edx_video_id'],
                'status': new_status,
                'message': message
            }
        ])
    elif video['status'] == 'invalid_token':
        status = StatusDisplayStrings.get('youtube_duplicate')
    else:
        status = StatusDisplayStrings.get(video['status'])

    return status


def _get_videos(course):
    """
    Retrieves the list of videos from VAL corresponding to this course.
    """
    videos = list(get_videos_for_course(course.id, VideoSortField.created, SortDirection.desc))

    # convert VAL's status to studio's Video Upload feature status.
    for video in videos:
        video["status"] = convert_video_status(video)

    return videos


def _get_index_videos(course):
    """
    Returns the information about each video upload required for the video list
    """
    return list(
        {
            attr: video[attr]
            for attr in ["edx_video_id", "client_video_id", "created", "duration", "status"]
        }
        for video in _get_videos(course)
    )


def videos_index_html(course):
    """
    Returns an HTML page to display previous video uploads and allow new ones
    """
    return render_to_response(
        "videos_index.html",
        {
            "context_course": course,
            # temporarily using assets url to test frontend
            "image_upload_url": reverse_course_url('video_images_handler', unicode(course.id)),
            "video_handler_url": reverse_course_url("videos_handler", unicode(course.id)),
            "encodings_download_url": reverse_course_url("video_encodings_download", unicode(course.id)),
            "previous_uploads": _get_index_videos(course),
            "concurrent_upload_limit": settings.VIDEO_UPLOAD_PIPELINE.get("CONCURRENT_UPLOAD_LIMIT", 0),
            "video_supported_file_formats": VIDEO_SUPPORTED_FILE_FORMATS.keys(),
            "video_upload_max_file_size": VIDEO_UPLOAD_MAX_FILE_SIZE_GB
        }
    )


def videos_index_json(course):
    """
    Returns JSON in the following format:
    {
        "videos": [{
            "edx_video_id": "aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
            "client_video_id": "video.mp4",
            "created": "1970-01-01T00:00:00Z",
            "duration": 42.5,
            "status": "upload"
        }]
    }
    """
    return JsonResponse({"videos": _get_index_videos(course)}, status=200)


def videos_post(course, request):
    """
    Input (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "content_type": "video/mp4"
        }]
    }

    Returns (JSON):
    {
        "files": [{
            "file_name": "video.mp4",
            "upload_url": "http://example.com/put_video"
        }]
    }

    The returned array corresponds exactly to the input array.
    """
    error = None
    if "files" not in request.json:
        error = "Request object is not JSON or does not contain 'files'"
    elif any(
            "file_name" not in file or "content_type" not in file
            for file in request.json["files"]
    ):
        error = "Request 'files' entry does not contain 'file_name' and 'content_type'"
    elif any(
            file['content_type'] not in VIDEO_SUPPORTED_FILE_FORMATS.values()
            for file in request.json["files"]
    ):
        error = "Request 'files' entry contain unsupported content_type"

    if error:
        return JsonResponse({"error": error}, status=400)

    bucket = storage_service_bucket()
    course_video_upload_token = course.video_upload_pipeline["course_video_upload_token"]
    req_files = request.json["files"]
    resp_files = []

    for req_file in req_files:
        file_name = req_file["file_name"]

        try:
            file_name.encode('ascii')
        except UnicodeEncodeError:
            error_msg = 'The file name for %s must contain only ASCII characters.' % file_name
            return JsonResponse({'error': error_msg}, status=400)

        edx_video_id = unicode(uuid4())
        key = storage_service_key(bucket, file_name=edx_video_id)
        for metadata_name, value in [
                ("course_video_upload_token", course_video_upload_token),
                ("client_video_id", file_name),
                ("course_key", unicode(course.id)),
        ]:
            key.set_metadata(metadata_name, value)
        upload_url = key.generate_url(
            KEY_EXPIRATION_IN_SECONDS,
            "PUT",
            headers={"Content-Type": req_file["content_type"]}
        )

        # persist edx_video_id in VAL
        create_video({
            "edx_video_id": edx_video_id,
            "status": "upload",
            "client_video_id": file_name,
            "duration": 0,
            "encoded_videos": [],
            "courses": [course.id]
        })

        resp_files.append({"file_name": file_name, "upload_url": upload_url, "edx_video_id": edx_video_id})

    return JsonResponse({"files": resp_files}, status=200)


def storage_service_bucket():
    """
    Returns an S3 bucket for video uploads.
    """
    conn = s3.connection.S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
    )
    return conn.get_bucket(settings.VIDEO_UPLOAD_PIPELINE["BUCKET"])


def storage_service_key(bucket, file_name):
    """
    Returns an S3 key to the given file in the given bucket.
    """
    key_name = "{}/{}".format(
        settings.VIDEO_UPLOAD_PIPELINE.get("ROOT_PATH", ""),
        file_name
    )
    return s3.key.Key(bucket, key_name)


def send_video_status_update(updates):
    """
    Update video status in edx-val.
    """
    for update in updates:
        update_video_status(update.get('edxVideoId'), update.get('status'))
        LOGGER.info(
            'VIDEOS: Video status update with id [%s], status [%s] and message [%s]',
            update.get('edxVideoId'),
            update.get('status'),
            update.get('message')
        )

    return JsonResponse()


def is_status_update_request(request_data):
    """
    Returns True if `request_data` contains status update else False.
    """
    return any('status' in update for update in request_data)
