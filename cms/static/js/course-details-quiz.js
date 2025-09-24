/**
 * Course Details and Quiz Management for Course Outline
 * Extends the course outline functionality with course detail editing and quiz creation
 */
define(['jquery', 'underscore', 'gettext'], function($, _, gettext) {
    'use strict';

    var CourseDetailsManager = {
        courseKey: null,
        
        init: function(courseKey) {
            console.log('CourseDetailsManager.init called with courseKey:', courseKey);
            this.courseKey = courseKey;
            this.bindEvents();
            
            // Check if course details section exists
            var courseDetailsSection = $('.course-details-section');
            if (courseDetailsSection.length === 0) {
                console.warn('Course details section not found in DOM');
                return;
            }
            
            console.log('Course details section found, loading details...');
            this.loadCourseDetails();
        },

        bindEvents: function() {
            var self = this;
            
            // Course details editing
            $('.button-edit-course-details').on('click', function(e) {
                e.preventDefault();
                self.openCourseDetailsModal();
            });

            // Quiz management
            $(document).on('click', '.button-create-quiz', function(e) {
                e.preventDefault();
                var subsectionId = $(this).data('subsection-id');
                var subsectionTitle = $(this).data('subsection-title');
                self.openQuizModal(subsectionId, subsectionTitle);
            });

            $(document).on('click', '.quiz-action-btn.edit', function(e) {
                e.preventDefault();
                var quizId = $(this).data('quiz-id');
                self.editQuiz(quizId);
            });

            $(document).on('click', '.quiz-action-btn.delete', function(e) {
                e.preventDefault();
                var quizId = $(this).data('quiz-id');
                self.deleteQuiz(quizId);
            });
        },

        loadCourseDetails: function() {
            var self = this;
            var apiUrl = '/api/chalix/dashboard/course-detail/' + encodeURIComponent(this.courseKey) + '/';
            
            console.log('Loading course details from:', apiUrl);
            console.log('Course key:', this.courseKey);
            
            $.ajax({
                url: apiUrl,
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() || $('[name="csrftoken"]').attr('content')
                }
            })
                .done(function(data) {
                    console.log('Course details loaded successfully:', data);
                    self.displayCourseDetails(data);
                })
                .fail(function(xhr, status, error) {
                    console.error('Failed to load course details:', {
                        status: xhr.status,
                        statusText: xhr.statusText,
                        error: error,
                        response: xhr.responseText
                    });
                    // Show empty state when no course details are found
                    self.displayCourseDetails({});
                });
        },

        displayCourseDetails: function(data) {
            console.log('Displaying course details:', data);
            
            var estimatedHours = data.estimated_hours || gettext('Chưa đặt');
            var onlineLink = data.online_course_link || gettext('Chưa đặt');
            var instructor = data.instructor || gettext('Chưa đặt');
            
            console.log('Setting values:', {
                estimatedHours: estimatedHours,
                onlineLink: onlineLink,
                instructor: instructor
            });
            
            $('#display-estimated-hours').text(estimatedHours);
            $('#display-online-meeting-link').text(onlineLink);
            $('#display-assigned-instructor').text(instructor);
        },

        openCourseDetailsModal: function() {
            var self = this;
            
            // Reuse the same modal from the dashboard
            var modalHtml = this.getCourseDetailsModalHtml();
            $('body').append(modalHtml);
            
            var modal = $('#edit-course-modal');
            
            // Load current course details into the modal
            $.get('/api/chalix/dashboard/course-detail/' + this.courseKey + '/')
                .done(function(data) {
                    modal.find('[name="estimated_hours"]').val(data.estimated_hours || '');
                    modal.find('[name="online_course_link"]').val(data.online_course_link || '');
                    modal.find('[name="instructor"]').val(data.instructor || '');
                });

            modal.addClass('is-shown');
            
            // Handle modal close
            modal.find('.modal-close, .cancel-button').on('click', function() {
                modal.removeClass('is-shown').remove();
            });

            // Handle save
            modal.find('.save-button').on('click', function() {
                self.saveCourseDetails(modal);
            });
        },

        refreshQuizList: function(subsectionId) {
            var self = this;
            var quizSection = $('.quiz-section[data-subsection-id="' + subsectionId + '"]');
            
            if (!this.courseKey) {
                console.warn('No course key available for loading quizzes');
                return;
            }
            
            // Load quizzes for this subsection
            $.ajax({
                url: '/api/chalix/quiz/list/' + encodeURIComponent(this.courseKey) + '/',
                method: 'GET',
                data: { parent_locator: subsectionId },
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() || $('[name="csrftoken"]').attr('content')
                }
            })
            .done(function(response) {
                if (response.success && response.quizzes) {
                    var quizListHtml = '<ul class="quiz-list">';
                    
                    if (response.quizzes.length === 0) {
                        quizListHtml += '<li class="quiz-empty-state">' + gettext('No quizzes created yet') + '</li>';
                    } else {
                        response.quizzes.forEach(function(quiz) {
                            quizListHtml += `
                                <li class="quiz-item">
                                    <div class="quiz-item-content">
                                        <h5 class="quiz-question">${quiz.title}</h5>
                                        <div class="quiz-meta">${quiz.question_count} questions</div>
                                    </div>
                                    <div class="quiz-actions">
                                        <button class="quiz-action-btn edit" data-quiz-id="${quiz.id}">${gettext('Edit')}</button>
                                        <button class="quiz-action-btn delete" data-quiz-id="${quiz.id}">${gettext('Delete')}</button>
                                    </div>
                                </li>
                            `;
                        });
                    }
                    
                    quizListHtml += '</ul>';
                    quizSection.find('.quiz-list').remove();
                    quizSection.append(quizListHtml);
                }
            })
            .fail(function(xhr) {
                console.error('Failed to load quizzes for subsection:', subsectionId, xhr);
            });
        },

        getCourseDetailsModalHtml: function() {
            return `
                <div id="edit-course-modal" class="modal course-edit-modal">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2 class="modal-title">${gettext('Edit Course Details')}</h2>
                            <button class="modal-close" type="button">&times;</button>
                        </div>
                        <div class="modal-body">
                            <form class="edit-course-form">
                                <div class="form-row">
                                    <div class="form-group">
                                        <label for="estimated_hours">${gettext('Estimated Hours to Complete')}</label>
                                        <input type="number" name="estimated_hours" id="estimated_hours" class="form-control" min="0" step="0.5" placeholder="${gettext('Enter estimated hours')}">
                                    </div>
                                    <div class="form-group">
                                        <label for="instructor">${gettext('Assigned Instructor (Chỉ định giảng viên)')}</label>
                                        <input type="text" name="instructor" id="instructor" class="form-control" placeholder="${gettext('Enter instructor name')}">
                                    </div>
                                </div>
                                <div class="form-group full-width">
                                    <label for="online_course_link">${gettext('Online Meeting Link')}</label>
                                    <input type="url" name="online_course_link" id="online_course_link" class="form-control" placeholder="${gettext('Enter meeting URL')}">
                                    <div class="help-text">${gettext('This field will always be visible in the edit interface')}</div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="button cancel-button">${gettext('Cancel')}</button>
                            <button type="button" class="button button-primary save-button">${gettext('Save Changes')}</button>
                        </div>
                    </div>
                </div>
            `;
        },

        saveCourseDetails: function(modal) {
            var self = this;
            var formData = {
                estimated_hours: modal.find('[name="estimated_hours"]').val(),
                online_course_link: modal.find('[name="online_course_link"]').val(),
                instructor: modal.find('[name="instructor"]').val(),
                course_key: this.courseKey
            };

            $.post('/api/chalix/dashboard/update-course/', formData)
                .done(function(data) {
                    self.displayCourseDetails(data);
                    modal.removeClass('is-shown').remove();
                    self.showSuccessMessage(gettext('Course details updated successfully!'));
                })
                .fail(function() {
                    self.showErrorMessage(gettext('Failed to update course details'));
                });
        },

        openQuizModal: function(subsectionId, subsectionTitle, quizData) {
            var self = this;
            var modalHtml = this.getQuizModalHtml(subsectionTitle, quizData);
            $('body').append(modalHtml);
            
            var modal = $('#quiz-modal');
            modal.addClass('is-shown');
            
            // Initialize with default choices if creating new quiz
            if (!quizData) {
                this.addQuizChoice(modal.find('.quiz-choices-container'));
                this.addQuizChoice(modal.find('.quiz-choices-container'));
            }

            // Handle events
            this.bindQuizModalEvents(modal, subsectionId, quizData);
        },

        getQuizModalHtml: function(subsectionTitle, quizData) {
            var isEdit = !!quizData;
            var modalTitle = isEdit ? gettext('Edit Quiz Question') : gettext('Create Quiz Question');
            var question = quizData ? quizData.question : '';
            var isMultiple = quizData ? quizData.is_multiple_choice : false;

            return `
                <div id="quiz-modal" class="quiz-modal">
                    <div class="quiz-modal-content">
                        <div class="quiz-modal-header">
                            <h3 class="quiz-modal-title">${modalTitle} - ${subsectionTitle}</h3>
                            <button class="quiz-modal-close">&times;</button>
                        </div>
                        <div class="quiz-modal-body">
                            <form class="quiz-form">
                                <div class="quiz-form-group">
                                    <label class="quiz-form-label">${gettext('Question')}</label>
                                    <textarea class="quiz-form-textarea" name="question" placeholder="${gettext('Enter your question here...')}" required>${question}</textarea>
                                </div>
                                
                                <div class="quiz-form-group">
                                    <label class="quiz-form-label">${gettext('Question Type')}</label>
                                    <div class="quiz-type-toggle">
                                        <div class="quiz-type-option">
                                            <input type="radio" name="quiz_type" value="single" id="quiz-single" class="quiz-type-radio" ${!isMultiple ? 'checked' : ''}>
                                            <label for="quiz-single" class="quiz-type-label">${gettext('Single Choice')}</label>
                                        </div>
                                        <div class="quiz-type-option">
                                            <input type="radio" name="quiz_type" value="multiple" id="quiz-multiple" class="quiz-type-radio" ${isMultiple ? 'checked' : ''}>
                                            <label for="quiz-multiple" class="quiz-type-label">${gettext('Multiple Choice')}</label>
                                        </div>
                                    </div>
                                </div>

                                <div class="quiz-form-group">
                                    <label class="quiz-form-label">${gettext('Answer Choices')}</label>
                                    <div class="quiz-choices-container">
                                        ${this.getChoicesHtml(quizData ? quizData.choices : [])}
                                    </div>
                                    <button type="button" class="quiz-add-choice">${gettext('Add Choice')}</button>
                                </div>
                            </form>
                        </div>
                        <div class="quiz-form-actions">
                            <button type="button" class="quiz-button-cancel">${gettext('Cancel')}</button>
                            <button type="button" class="quiz-button-save">${gettext('Save Quiz')}</button>
                        </div>
                    </div>
                </div>
            `;
        },

        getChoicesHtml: function(choices) {
            if (!choices || choices.length === 0) return '';
            
            return choices.map(function(choice, index) {
                return `
                    <div class="quiz-choice-item">
                        <input type="text" class="quiz-choice-input" value="${choice.text}" placeholder="${gettext('Enter choice text...')}" required>
                        <input type="checkbox" class="quiz-choice-correct" ${choice.is_correct ? 'checked' : ''} title="${gettext('Mark as correct answer')}">
                        <button type="button" class="quiz-choice-remove">&times;</button>
                    </div>
                `;
            }).join('');
        },

        bindQuizModalEvents: function(modal, subsectionId, quizData) {
            var self = this;

            // Close modal
            modal.find('.quiz-modal-close, .quiz-button-cancel').on('click', function() {
                modal.removeClass('is-shown').remove();
            });

            // Add choice
            modal.find('.quiz-add-choice').on('click', function() {
                self.addQuizChoice(modal.find('.quiz-choices-container'));
            });

            // Remove choice
            modal.on('click', '.quiz-choice-remove', function() {
                $(this).closest('.quiz-choice-item').remove();
            });

            // Quiz type change
            modal.find('[name="quiz_type"]').on('change', function() {
                var isMultiple = $(this).val() === 'multiple';
                var checkboxType = isMultiple ? 'checkbox' : 'radio';
                var checkboxName = isMultiple ? '' : 'correct_answer';
                
                modal.find('.quiz-choice-correct').attr('type', checkboxType).attr('name', checkboxName);
                
                if (!isMultiple) {
                    // Clear all checkboxes and allow only one selection for radio
                    modal.find('.quiz-choice-correct').prop('checked', false);
                }
            });

            // Save quiz
            modal.find('.quiz-button-save').on('click', function() {
                self.saveQuiz(modal, subsectionId, quizData);
            });
        },

        addQuizChoice: function(container) {
            var choiceHtml = `
                <div class="quiz-choice-item">
                    <input type="text" class="quiz-choice-input" placeholder="${gettext('Enter choice text...')}" required>
                    <input type="checkbox" class="quiz-choice-correct" title="${gettext('Mark as correct answer')}">
                    <button type="button" class="quiz-choice-remove">&times;</button>
                </div>
            `;
            container.append(choiceHtml);
        },

        saveQuiz: function(modal, subsectionId, existingQuizData) {
            var self = this;
            var formData = this.collectQuizFormData(modal);
            
            if (!this.validateQuizForm(formData)) {
                return;
            }

            formData.subsection_id = subsectionId;
            formData.course_key = this.courseKey;

            var url = existingQuizData ? 
                '/api/chalix/quiz/update/' + existingQuizData.id + '/' : 
                '/api/chalix/quiz/create/';

            $.post(url, JSON.stringify(formData), null, 'json')
                .done(function(data) {
                    modal.removeClass('is-shown').remove();
                    self.refreshQuizList(subsectionId);
                    self.showSuccessMessage(gettext('Quiz saved successfully!'));
                })
                .fail(function() {
                    self.showErrorMessage(gettext('Failed to save quiz'));
                });
        },

        collectQuizFormData: function(modal) {
            var question = modal.find('[name="question"]').val();
            var isMultiple = modal.find('[name="quiz_type"]:checked').val() === 'multiple';
            var choices = [];

            modal.find('.quiz-choice-item').each(function() {
                var text = $(this).find('.quiz-choice-input').val();
                var isCorrect = $(this).find('.quiz-choice-correct').is(':checked');
                if (text.trim()) {
                    choices.push({
                        text: text.trim(),
                        is_correct: isCorrect
                    });
                }
            });

            return {
                question: question,
                is_multiple_choice: isMultiple,
                choices: choices
            };
        },

        validateQuizForm: function(formData) {
            if (!formData.question.trim()) {
                this.showErrorMessage(gettext('Please enter a question'));
                return false;
            }

            if (formData.choices.length < 2) {
                this.showErrorMessage(gettext('Please provide at least 2 choices'));
                return false;
            }

            var hasCorrectAnswer = formData.choices.some(function(choice) {
                return choice.is_correct;
            });

            if (!hasCorrectAnswer) {
                this.showErrorMessage(gettext('Please mark at least one correct answer'));
                return false;
            }

            return true;
        },

        editQuiz: function(quizId) {
            var self = this;
            $.get('/api/chalix/quiz/' + quizId + '/')
                .done(function(quizData) {
                    self.openQuizModal(quizData.subsection_id, quizData.subsection_title, quizData);
                })
                .fail(function() {
                    self.showErrorMessage(gettext('Failed to load quiz data'));
                });
        },

        deleteQuiz: function(quizId) {
            var self = this;
            if (confirm(gettext('Are you sure you want to delete this quiz?'))) {
                $.ajax({
                    url: '/api/chalix/quiz/delete/' + quizId + '/',
                    type: 'DELETE'
                })
                .done(function() {
                    $('[data-quiz-id="' + quizId + '"]').closest('.quiz-item').remove();
                    self.showSuccessMessage(gettext('Quiz deleted successfully!'));
                })
                .fail(function() {
                    self.showErrorMessage(gettext('Failed to delete quiz'));
                });
            }
        },

        refreshQuizList: function(subsectionId) {
            var self = this;
            $.get('/api/chalix/quiz/list/' + subsectionId + '/')
                .done(function(quizzes) {
                    self.updateQuizDisplay(subsectionId, quizzes);
                });
        },

        updateQuizDisplay: function(subsectionId, quizzes) {
            var container = $('[data-subsection-id="' + subsectionId + '"] .quiz-list');
            container.empty();

            if (quizzes.length === 0) {
                container.append('<div class="quiz-empty-state">' + gettext('No quizzes created yet') + '</div>');
            } else {
                quizzes.forEach(function(quiz) {
                    var quizHtml = `
                        <div class="quiz-item">
                            <div class="quiz-item-content">
                                <div class="quiz-question">${quiz.question}</div>
                                <div class="quiz-meta">${quiz.choices.length} ${gettext('choices')} • ${quiz.is_multiple_choice ? gettext('Multiple choice') : gettext('Single choice')}</div>
                            </div>
                            <div class="quiz-actions">
                                <button class="quiz-action-btn edit" data-quiz-id="${quiz.id}">${gettext('Edit')}</button>
                                <button class="quiz-action-btn delete" data-quiz-id="${quiz.id}">${gettext('Delete')}</button>
                            </div>
                        </div>
                    `;
                    container.append(quizHtml);
                });
            }
        },

        showSuccessMessage: function(message) {
            // Create a temporary success notification
            var notification = $('<div class="notification success">' + message + '</div>');
            $('body').append(notification);
            setTimeout(function() {
                notification.fadeOut(function() {
                    notification.remove();
                });
            }, 3000);
        },

        showErrorMessage: function(message) {
            // Create a temporary error notification
            var notification = $('<div class="notification error">' + message + '</div>');
            $('body').append(notification);
            setTimeout(function() {
                notification.fadeOut(function() {
                    notification.remove();
                });
            }, 5000);
        }
    };

    // Extend the course outline to include quiz sections
    var QuizIntegration = {
        init: function() {
            this.addQuizSectionsToOutline();
            this.loadExistingQuizzes();
        },

        addQuizSectionsToOutline: function() {
            // Add quiz sections to each subsection in the outline
            $('.outline-subsection').each(function() {
                var $subsection = $(this);
                var subsectionId = $subsection.data('locator');
                var subsectionTitle = $subsection.find('.subsection-header-title').text().trim();
                
                if (subsectionId && subsectionTitle) {
                    var quizSectionHtml = `
                        <div class="quiz-section" data-subsection-id="${subsectionId}">
                            <div class="quiz-header">
                                <h4 class="quiz-title">${gettext('Câu hỏi trắc nghiệm')}</h4>
                                <button class="button-create-quiz" data-subsection-id="${subsectionId}" data-subsection-title="${subsectionTitle}">
                                    <span class="icon fa fa-plus" aria-hidden="true"></span>${gettext('Create Quiz')}
                                </button>
                            </div>
                            <div class="quiz-list">
                                <div class="quiz-empty-state">${gettext('No quizzes created yet')}</div>
                            </div>
                        </div>
                    `;
                    
                    $subsection.append(quizSectionHtml);
                }
            });
        },

        loadExistingQuizzes: function() {
            var self = this;
            $('.quiz-section').each(function() {
                var subsectionId = $(this).data('subsection-id');
                if (subsectionId) {
                    CourseDetailsManager.refreshQuizList(subsectionId);
                }
            });
        }
    };

    return {
        CourseDetailsManager: CourseDetailsManager,
        QuizIntegration: QuizIntegration
    };
});