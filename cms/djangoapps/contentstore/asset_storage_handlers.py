"""Views for assets"""


from django.core.exceptions import PermissionDenied

from opaque_keys.edx.keys import AssetKey, CourseKey
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator

from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.json_request import JsonResponse
from xmodule.contentstore.content import StaticContent  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order


def get_asset_usage_path_json(request, course_key, asset_key_string):
    """
    Get a list of units with ancestors that use given asset.
    """
    course_key = CourseKey.from_string(course_key)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()
    asset_location = AssetKey.from_string(asset_key_string) if asset_key_string else None
    usage_locations = _get_asset_usage_path(course_key, [{'asset_key': asset_location}])
    return JsonResponse({'usage_locations': usage_locations})


def _get_asset_usage_path(course_key, assets):
    """
    Get a list of units with ancestors that use given asset.
    """
    store = modulestore()
    usage_locations = {str(asset['asset_key']): [] for asset in assets}

    # Check in all course blocks
    verticals = store.get_items(
        course_key,
        qualifiers={
            'category': 'vertical'
        },
    )
    blocks = []

    for vertical in verticals:
        blocks.extend(vertical.get_children())

    for block in blocks:
        for asset in assets:
            try:
                asset_key = asset['asset_key']
                asset_key_string = str(asset_key)
                current_locations = usage_locations[asset_key_string]
                asset_block_found = _locate_asset_in_block(asset, block)

                if isinstance(asset_block_found, list):
                    usage_locations[asset_key_string] = [
                        *current_locations
                    ]
                    for location_asset_found in asset_block_found:
                        usage_locations[asset_key_string].append(location_asset_found)
                elif asset_block_found is not None:
                    usage_locations[asset_key_string] = [
                        *current_locations, asset_block_found
                    ]
            except AttributeError:
                continue
    return usage_locations


def _locate_asset_in_block(asset, block):
    """
    Check to see if an asset exists in a block.
    """
    asset_key = asset['asset_key']
    asset_key_string = str(asset_key)
    static_path = StaticContent.get_static_path_from_location(asset_key)
    is_video_block = getattr(block, 'category', '') == 'video'
    is_openassessment_block = getattr(block, 'category', '') == 'openassessment'
    is_library_content_block = getattr(block, 'category', '') == 'library_content'

    if is_video_block:
        handout = getattr(block, 'handout', '')
        if handout and asset_key_string in handout:
            return _get_asset_usage_block_info(block)

    elif is_openassessment_block:
        prompt = getattr(block, 'prompt', '')
        if static_path in prompt or asset_key_string in prompt:
            return _get_asset_usage_block_info(block)

        rubric_feedback_default_text = getattr(block, 'rubric_feedback_default_text', '')
        if static_path in rubric_feedback_default_text or asset_key_string in rubric_feedback_default_text:
            return _get_asset_usage_block_info(block)

        rubric_feedback_prompt = getattr(block, 'rubric_feedback_prompt', '')
        if static_path in rubric_feedback_prompt or asset_key_string in rubric_feedback_prompt:
            return _get_asset_usage_block_info(block)

    elif is_library_content_block:
        library_asset_blocks = []
        for child_block in getattr(block, 'children', ''):
            asset_child_block_found = _locate_asset_in_block(
                asset,
                modulestore().get_item(child_block)
            )
            if asset_child_block_found is not None:
                library_asset_blocks.append(asset_child_block_found)
        return library_asset_blocks

    else:
        data = getattr(block, 'data', '')
        if static_path in data or asset_key_string in data:
            return _get_asset_usage_block_info(block)


def _get_asset_usage_block_info(block):
    """
    Get the location for an image for a given block.
    """
    usage_dict = {'display_location': '', 'url': ''}
    xblock_display_name = getattr(block, 'display_name', '')
    xblock_location = str(block.location)
    unit = block.get_parent()
    unit_location = str(block.parent)
    unit_display_name = getattr(unit, 'display_name', '')
    subsection = unit.get_parent()
    subsection_display_name = getattr(subsection, 'display_name', '')
    usage_dict['display_location'] = (f'{subsection_display_name} - '
                                        f'{unit_display_name} / {xblock_display_name}')
    usage_dict['url'] = f'/container/{unit_location}#{xblock_location}'

    return usage_dict

