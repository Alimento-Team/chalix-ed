define(['domReady', 'jquery', 'underscore', 'js/utils/cancel_on_escape', 'js/views/utils/create_course_utils',
    'js/views/utils/create_library_utils', 'common/js/components/utils/view_utils'],
function(domReady, $, _, CancelOnEscape, CreateCourseUtilsFactory, CreateLibraryUtilsFactory, ViewUtils) {
    'use strict';

    var CreateCourseUtils = new CreateCourseUtilsFactory({
        name: '.new-course-name',
        org: '.new-course-org',
        number: '.new-course-number',
        run: '.new-course-run',
        save: '.new-course-save',
        errorWrapper: '.create-course .wrap-error',
        errorMessage: '#course_creation_error',
        tipError: '.create-course span.tip-error',
        error: '.create-course .error',
        allowUnicode: '.allow-unicode-course-id'
    }, {
        shown: 'is-shown',
        showing: 'is-showing',
        hiding: 'is-hiding',
        disabled: 'is-disabled',
        error: 'error'
    });

    var CreateLibraryUtils = new CreateLibraryUtilsFactory({
        name: '.new-library-name',
        org: '.new-library-org',
        number: '.new-library-number',
        save: '.new-library-save',
        errorWrapper: '.create-library .wrap-error',
        errorMessage: '#library_creation_error',
        tipError: '.create-library  span.tip-error',
        error: '.create-library .error',
        allowUnicode: '.allow-unicode-library-id'
    }, {
        shown: 'is-shown',
        showing: 'is-showing',
        hiding: 'is-hiding',
        disabled: 'is-disabled',
        error: 'error'
    });

    var loadProfessionalFields = function() {
        // Load professional fields from API
        $.ajax({
            url: '/api/cms/v1/professional_fields/',
            method: 'GET',
            success: function(response) {
                var $select = $('.new-course-professional-field');
                $select.find('option:not(:first)').remove(); // Clear existing options except placeholder
                
                if (response.professional_fields && response.professional_fields.length > 0) {
                    response.professional_fields.forEach(function(field) {
                        $select.append($('<option>', {
                            value: field.id,
                            text: field.name
                        }));
                    });
                } else {
                    // No professional fields available
                    $select.append($('<option>', {
                        value: '',
                        text: '(Chưa có lĩnh vực nào)',
                        disabled: true
                    }));
                }
            },
            error: function() {
                console.error('Failed to load professional fields');
            }
        });
    };

    var saveNewCourse = function(e) {
        e.preventDefault();

        if (CreateCourseUtils.hasInvalidRequiredFields()) {
            return;
        }

        var $newCourseForm = $(this).closest('#create-course-form');
        var display_name = $newCourseForm.find('.new-course-name').val();
        var org = $newCourseForm.find('.new-course-org').val();
        var number = $newCourseForm.find('.new-course-number').val();
        var run = $newCourseForm.find('.new-course-run').val();
        var course_category = $newCourseForm.find('.new-course-category').val();
        var professional_field_id = $newCourseForm.find('.new-course-professional-field').val();

        // Check if course_category field exists and is required (for 'bộ' role)
        var $courseCategoryField = $newCourseForm.find('#field-course-category');
        if ($courseCategoryField.length && !course_category) {
            // Show error for missing course category
            $courseCategoryField.find('.tip-error').text('Vui lòng chọn loại khoá học').removeClass('is-hidden');
            $courseCategoryField.addClass('error');
            return;
        }

        // Check if professional_field is required (for all roles)
        var $professionalFieldField = $newCourseForm.find('#field-professional-field');
        if ($professionalFieldField.length && !professional_field_id) {
            // Show error for missing professional field
            $professionalFieldField.find('.tip-error').text('Vui lòng chọn lĩnh vực chuyên môn').removeClass('is-hidden');
            $professionalFieldField.addClass('error');
            return;
        }

        var course_info = {
            org: org,
            number: number,
            display_name: display_name,
            run: run
        };

        // Add course_category only if it exists
        if (course_category) {
            course_info.course_category = course_category;
            // Also set publish_type for backwards compatibility
            course_info.publish_type = course_category;
        }

        // Add professional_field_id if selected
        if (professional_field_id) {
            course_info.professional_field_id = professional_field_id;
        }

        analytics.track('Created a Course', course_info);
        CreateCourseUtils.create(course_info, function(errorMessage) {
            var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
            $('.create-course .wrap-error').addClass('is-shown');
            edx.HtmlUtils.setHtml($('#course_creation_error'), msg);
            $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
        });
    };

    var rtlTextDirection = function() {
        var Selectors = {
            new_course_run: '#new-course-run'
        };

        if ($('body').hasClass('rtl')) {
            $(Selectors.new_course_run).addClass('course-run-text-direction placeholder-text-direction');
            $(Selectors.new_course_run).on('input', function() {
                if (this.value === '') {
                    $(Selectors.new_course_run).addClass('placeholder-text-direction');
                } else {
                    $(Selectors.new_course_run).removeClass('placeholder-text-direction');
                }
            });
        }
    };

    var makeCancelHandler = function(addType) {
        return function(e) {
            e.preventDefault();
            $('.new-' + addType + '-button').removeClass('is-disabled').attr('aria-disabled', false);
            $('.wrapper-create-' + addType).removeClass('is-shown');
            // Clear out existing fields and errors
            $('#create-' + addType + '-form input[type=text]').val('');
            $('#' + addType + '_creation_error').html('');
            $('.create-' + addType + ' .wrap-error').removeClass('is-shown');
            $('.new-' + addType + '-save').off('click');
        };
    };

    var addNewCourse = function(e) {
        var $newCourse,
            $cancelButton,
            $courseName;
        e.preventDefault();
        $('.new-course-button').addClass('is-disabled').attr('aria-disabled', true);
        $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
        $newCourse = $('.wrapper-create-course').addClass('is-shown');
        $cancelButton = $newCourse.find('.new-course-cancel');
        $courseName = $('.new-course-name');
        $courseName.focus().select();
        $('.new-course-save').on('click', saveNewCourse);
        $cancelButton.bind('click', makeCancelHandler('course'));
        CancelOnEscape($cancelButton);
        CreateCourseUtils.setupOrgAutocomplete();
        CreateCourseUtils.configureHandlers();
        rtlTextDirection();
        
        // Load professional fields for dropdown
        loadProfessionalFields();
    };

    var saveNewLibrary = function(e) {
        e.preventDefault();

        if (CreateLibraryUtils.hasInvalidRequiredFields()) {
            return;
        }

        var $newLibraryForm = $(this).closest('#create-library-form');
        var display_name = $newLibraryForm.find('.new-library-name').val();
        var org = $newLibraryForm.find('.new-library-org').val();
        var number = $newLibraryForm.find('.new-library-number').val();

        var lib_info = {
            org: org,
            number: number,
            display_name: display_name
        };

        analytics.track('Created a Library', lib_info);
        CreateLibraryUtils.create(lib_info, function(errorMessage) {
            var msg = edx.HtmlUtils.joinHtml(edx.HtmlUtils.HTML('<p>'), errorMessage, edx.HtmlUtils.HTML('</p>'));
            $('.create-library .wrap-error').addClass('is-shown');
            edx.HtmlUtils.setHtml($('#library_creation_error'), msg);
            $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
        });
    };

    var addNewLibrary = function(e) {
        e.preventDefault();
        $('.new-library-button').addClass('is-disabled').attr('aria-disabled', true);
        $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
        var $newLibrary = $('.wrapper-create-library').addClass('is-shown');
        var $cancelButton = $newLibrary.find('.new-library-cancel');
        var $libraryName = $('.new-library-name');
        $libraryName.focus().select();
        $('.new-library-save').on('click', saveNewLibrary);
        $cancelButton.bind('click', makeCancelHandler('library'));
        CancelOnEscape($cancelButton);

        CreateLibraryUtils.configureHandlers();
    };

    var showTab = function(tab) {
        return function(e) {
            e.preventDefault();
            window.location.hash = tab;
            $('.courses-tab').toggleClass('active', tab === 'courses-tab');
            $('.archived-courses-tab').toggleClass('active', tab === 'archived-courses-tab');
            $('.libraries-tab').toggleClass('active', tab === 'libraries-tab');

            // Also toggle this course-related notice shown below the course tab, if it is present:
            $('.wrapper-creationrights').toggleClass('is-hidden', tab !== 'courses-tab');
        };
    };

    var onReady = function() {
        var courseTabHref = $('#course-index-tabs .courses-tab a').attr('href');
        var libraryTabHref = $('#course-index-tabs .libraries-tab a').attr('href');
        var ArchivedTabHref = $('#course-index-tabs .archived-courses-tab a').attr('href');

        $('.new-course-button').bind('click', addNewCourse);
        $('.new-library-button').bind('click', addNewLibrary);

        $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function() {
            ViewUtils.reload();
        }));

        $('.action-reload').bind('click', ViewUtils.reload);

        if (courseTabHref === '#') {
            $('#course-index-tabs .courses-tab').bind('click', showTab('courses-tab'));
        }

        if (libraryTabHref === '#') {
            $('#course-index-tabs .libraries-tab').bind('click', showTab('libraries-tab'));
        }

        if (ArchivedTabHref === '#') {
            $('#course-index-tabs .archived-courses-tab').bind('click', showTab('archived-courses-tab'));
        }
        if (window.location.hash) {
            $(window.location.hash.replace('#', '.')).first('a').trigger('click');
        }
    };

    domReady(onReady);

    return {
        onReady: onReady
    };
});
