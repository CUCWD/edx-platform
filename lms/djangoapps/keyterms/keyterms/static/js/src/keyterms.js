/* Javascript for KeytermsXBlock. */
function KeytermsXBlock(runtime, element) {
    // Getting the handles for the python functions
    var addkeywordhandlerUrl = runtime.handlerUrl(element, 'add_keyterm');
    var removekeywordhandlerUrl = runtime.handlerUrl(element, 'remove_keyterm');
    var editlessonhandlerUrl = runtime.handlerUrl(element, 'edit_lesson');
    var getincludedkeytermshandlerUrl = runtime.handlerUrl(element, 'get_included_keyterms');

    // Stroing all keyterms for the course.
    var keytermsJson;
    var allKeytermsList = new Set();
    var includedKeytermsList = new Set();
    var courseid;

    // Used to update the keyterms html
    function updateSummary(result) {
        html = $.parseHTML(result.lessonsummary);
        $('.lessonsummary').html(html);
    }

    // Used to update the keyterms html
    function updateKeyterms(result) {
        html = $.parseHTML(result.keytermhtml);
        $('.allKeytermsList').html(html);
    }

    // Used for getting courseID
    function getStringBetween(str, start, end) {
        const result = str.match(new RegExp(start + "(.*)" + end));
        return result[1];
    }

    // Gets the information about a specific keyterm
    function getKeyTermInfo(keyterm) {
        for (var i = 0; i < keytermsJson.length; i++) {
            if (keytermsJson[i]["key_name"] === keyterm) {
                return keytermsJson[i];
            }
        }
    }

    // Editing lesson summary
    $(".editLessonSummary").click(function(eventObject) {
        var lesson = $(".lesson-field").val();
        var data = {lessonsummary: lesson};

        $.ajax({
            type: "POST",
            url: editlessonhandlerUrl,
            data: JSON.stringify(data),
            success: updateSummary
        });
    });
     
    function populateOptions(result) {
        var available = $('#id_keyterms_from');
        var chosen = $('#id_keyterms_to');

        allKeytermsList.forEach(term => {
            if ((result.includedKeytermsList).includes(term)){
                $(chosen).append(`<option value="${term}" title="${term}">${term}</option>`);
            } else {
                $(available).append(`<option value="${term}" title="${term}">${term}</option>`);
            }
        });

        // Create event handlers for the options
        $('#id_keyterms_input').change(function(){
            var select = $('#id_keyterms_from');
            for (var i = 0; i < select.length; i++) {
                var txt = select.options[i].text;
                var include = txt.toLowerCase().search($(this).val().toLowerCase());
                select.options[i].style.display = include ? 'inline-block':'none';
            }
        });

        $('#id_keyterms_add_link').click(function() {
            var arr = $(available).map(function(){
                return this.value;
            }).get();
            arr.forEach(term => {
                data = {keyterm:term}
                $.ajax({
                    type: "POST",
                    url: addkeywordhandlerUrl,
                    data: JSON.stringify(data),
                    success: updateKeyterms
                });
            });
        });
    }

    // initializing the data
    $(document).ready(function(){
        // Getting courseid
        const url = window.location.href;
        courseid = getStringBetween(url, 'block\-v1:', 'type').slice(0,-1);

        // Getting all the keyterms
        resturl = 'http://localhost:18500/api/v1/course_terms/?course_id=course-v1:'+ encodeURIComponent(courseid);
        $.getJSON(resturl,
        function(data, err) {
            keytermsJson = data;
            // Store list of all keyterms
            keytermsJson.forEach( keyterm => allKeytermsList.add(keyterm["key_name"]));
        }).then(data=>
            { 
                // Showing information about definition on hover
                $(".keytermli").each(function() {
                    const keyterm = $(this).attr('id');
                    var keyterminfo = getKeyTermInfo(keyterm);

                    // Definitions
                    var formattedContent = `<div class="outline-box"><h1>Definitions</h1><ul class="bullets">`;
                    keyterminfo["definitions"].forEach(definition => {
                        formattedContent += `<li>${definition["description"]}</li>`
                    })
                    formattedContent += `</ul></div>`;

                    // Textbooks
                    formattedContent += `<div class="outline-box"><h1>Textbooks</h1>`
                    keyterminfo["textbooks"].forEach(textbook => {
                        formattedContent += `<a href='${textbook["textbook_link"]}' class="btn">`
                        formattedContent += `${textbook["chapter"]}\n(Page ${textbook["page_num"]})`
                        formattedContent += `</a>`
                    })
                    formattedContent += `</div>`;

                    // Lessons
                    formattedContent += `<div class="outline-box"><h1>Lesson Pages</h1>`
                    /*
                    keyterminfo["lessons"].forEach(lesson => {
                        formattedContent += `<p>${lesson[""]}</p>`
                    })
                    */
                    formattedContent += `</div>`;

                    // Resources
                    formattedContent += `<div class="outline-box"><h1>Resources</h1><ul class="bullets">`
                    keyterminfo["resources"].forEach(resource => {
                        formattedContent += `<li><a href="${resource["resource_link"]}">${resource["friendly_name"]}</a></li>`
                    })
                    formattedContent += `</ul></div>`;

                    // Setting up the popover
                    $(this).popover({
                        html : true,
                        content: formattedContent,
                        title: keyterm,
                        trigger: "manual",
                    }).on("mouseenter", function() {
                        var _this = this;
                        $(this).popover("show");
                        $(".popover").on("mouseleave", function() {
                          $(_this).popover('hide');
                        });
                    }).on("mouseleave", function() {
                        var _this = this;
                        setTimeout(function() {
                          if (!$(".popover:hover").length) {
                            $(_this).popover("hide");
                          }
                        }, 300);
                    });
                });

                // Enabling popovers
                $('[data-toggle="popover"]').popover({
                    container: 'html'
                })

                var data = {course_id: courseid};
                $.ajax({
                    type: "POST",
                    url: getincludedkeytermshandlerUrl,
                    data: JSON.stringify(data),
                    success: populateOptions
                });
            }
        )
    });
}

