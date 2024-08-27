from django.conf import settings


def get_estimated_time(modulestore, structure_key):
    import datetime
    total_time = datetime.timedelta(0)
    structure = modulestore.get_course(structure_key, depth=None)
    from xmodule.modulestore.django import modulestore
    try:
        import edxval.api as edxval_api
    except ImportError:
        edxval_api = None
    
    for module in structure.get_children(): 
        module_time = datetime.timedelta(0)

        if module.override_estimated_time == True: 
            total_time += module.estimated_time
            continue

        for lesson in module.get_children():
            lesson_time = datetime.timedelta(0)

            if lesson.override_estimated_time == True: 
                module_time += lesson.estimated_time
                continue

            for unit in lesson.get_children():
                unit_time = datetime.timedelta(0)

                if unit.override_estimated_time == True: 
                    lesson_time += unit.estimated_time
                    continue

                for xblock in unit.get_children():
                    # if the xblock is a video, change the estimated time to the video length
                    if xblock.category == 'video':
                        vid_time = 240
                        vid_url = xblock.edx_video_id

                        if xblock.youtube_id_1_0 != '' and settings.YOUTUBE_API_KEY != "PUT_YOUR_API_KEY_HERE":
                            try:
                                import urllib.request
                                import json
                                import isodate

                                vid_id = xblock.youtube_id_1_0
                                api_url="https://www.googleapis.com/youtube/v3/videos?id="+vid_id+"&key="+settings.YOUTUBE_API_KEY+"&part=contentDetails"

                                req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(req) as url:
                                    data = json.loads(url.read().decode())

                                vid_time = data['items'][0]['contentDetails']['duration']
                                vid_time = isodate.parse_duration(vid_time).total_seconds()

                            except Exception as e:
                                print(e)
                            
                        elif xblock.edx_video_id != '':
                            vid_info = edxval_api.get_video_info(vid_url)
                            vid_time = vid_info.get("duration", 240)
                        xblock.estimated_time = datetime.timedelta(seconds=int(vid_time))
                    
                    # if the xblock is a drag and drop change the estimated time to 5 minutes
                    if xblock.category == 'drag-and-drop-v2' and xblock.override_estimated_time == False \
                    and xblock.estimated_time == datetime.timedelta(minutes=1):
                        xblock.estimated_time = datetime.timedelta(minutes=5)

                    # if the block is open response change the estimated time to 10 minutes
                    if xblock.category == 'openassessment' and xblock.override_estimated_time == False \
                    and xblock.estimated_time == datetime.timedelta(minutes=1):
                        xblock.estimated_time = datetime.timedelta(minutes=10)

                    # if the block is open response change the estimated time to 10 minutes
                    if xblock.category == 'openassessment' and xblock.override_estimated_time == False \
                    and xblock.estimated_time == datetime.timedelta(minutes=1):
                        xblock.estimated_time = datetime.timedelta(minutes=10)

                    # if the block is a multiple choice change the estimated time to the number of problems times 1 minute
                    if xblock.category == 'problem' and xblock.override_estimated_time == False \
                    and xblock.estimated_time == datetime.timedelta(minutes=1):
                        xblock.estimated_time = datetime.timedelta(minutes=len(xblock.problem_types))

                    unit_time += xblock.estimated_time
                    modulestore().update_item(xblock, 4)

                unit.estimated_time = unit_time
                lesson_time += unit_time
                modulestore().update_item(unit, 4)

            lesson.estimated_time = lesson_time
            module_time += lesson_time
            modulestore().update_item(lesson, 4)

        module.estimated_time = module_time
        total_time += module_time
        modulestore().update_item(module, 4) 

    structure.estimated_time = total_time
    modulestore().update_item(structure, 4)

    return total_time