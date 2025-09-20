define(
    ['underscore', 'gettext', 'js/utils/date_utils', 'js/views/baseview', 'common/js/components/views/feedback_prompt',
        'common/js/components/views/feedback_notification', 'common/js/components/utils/view_utils', 'edx-ui-toolkit/js/utils/html-utils',
        'text!templates/previous-slide-upload.underscore'],
    function(_, gettext, DateUtils, BaseView, PromptView, NotificationView, ViewUtils, HtmlUtils, previousSlideUploadTemplate) {
        'use strict';

        var PreviousSlideUploadView = BaseView.extend({
            tagName: 'div',

            className: 'slide-row',

            events: {
                'click .remove-slide-button.action-button': 'removeSlide',
                'click .copy-public-url-btn': 'copyPublicUrl'
            },

            initialize: function(options) {
                this.template = HtmlUtils.template(previousSlideUploadTemplate);
                this.slideHandlerUrl = options.slideHandlerUrl;
            },

            render: function() {
                var renderedAttributes = {
                    created: DateUtils.renderDate(this.model.get('created')),
                    status: this.model.get('status'),
                    public_url: this.model.get('public_url')
                };
                HtmlUtils.setHtml(
                    this.$el,
                    this.template(
                        _.extend({}, this.model.attributes, renderedAttributes)
                    )
                );
                return this;
            },

            removeSlide: function(event) {
                var slideView = this;
                event.preventDefault();

                ViewUtils.confirmThenRunOperation(
                    gettext('Are you sure you want to remove this slide from the list?'),
                    gettext('Removing a slide from this list does not affect course content. Any content that uses a previously uploaded slide ID continues to display in the course.'), // eslint-disable-line max-len
                    gettext('Remove'),
                    function() {
                        ViewUtils.runOperationShowingMessage(
                            gettext('Removing'),
                            function() {
                                return $.ajax({
                                    url: slideView.slideHandlerUrl + '/' + slideView.model.get('slide_id'),
                                    type: 'DELETE'
                                }).done(function() {
                                    slideView.remove();
                                });
                            }
                        );
                    }
                );
            },

            copyPublicUrl: function(event) {
                event.preventDefault();
                var $btn = $(event.currentTarget);
                var url = $btn.data('url');
                // Use Clipboard API if available
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(url).then(function() {
                        $btn.siblings('.copy-success-message').fadeIn(200).delay(1000).fadeOut(200);
                    });
                } else {
                    // Fallback for older browsers
                    var $input = $('<input>');
                    $('body').append($input);
                    $input.val(url).select();
                    document.execCommand('copy');
                    $input.remove();
                    $btn.siblings('.copy-success-message').fadeIn(200).delay(1000).fadeOut(200);
                }
            }
        });

        return PreviousSlideUploadView;
    }
);