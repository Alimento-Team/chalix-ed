define(
    ['underscore', 'js/models/active_slide_upload', 'js/views/baseview', 'common/js/components/views/feedback_prompt',
        'edx-ui-toolkit/js/utils/html-utils', 'text!templates/active-slide-upload.underscore'],
    function(_, ActiveSlideUpload, BaseView, PromptView, HtmlUtils, activeSlideUploadTemplate) {
        'use strict';

        var STATUS_CLASSES = [
            {status: ActiveSlideUpload.STATUS_QUEUED, cls: 'queued'},
            {status: ActiveSlideUpload.STATUS_COMPLETED, cls: 'success'},
            {status: ActiveSlideUpload.STATUS_FAILED, cls: 'error'}
        ];

        var ActiveSlideUploadView = BaseView.extend({
            tagName: 'li',
            className: 'active-slide-upload',

            events: {
                'click a.more-details-action': 'showUploadFailureMessage'
            },

            initialize: function() {
                this.template = HtmlUtils.template(activeSlideUploadTemplate);
                this.listenTo(this.model, 'change', this.render);
            },

            render: function() {
                var $el = this.$el,
                    status;
                HtmlUtils.setHtml($el, this.template(this.model.attributes));
                status = this.model.get('status');
                _.each(
                    STATUS_CLASSES,
                    function(statusClass) {
                        $el.toggleClass(statusClass.cls, status == statusClass.status);
                    }
                );
                return this;
            },

            showUploadFailureMessage: function() {
                return new PromptView.Warning({
                    title: gettext('Your file could not be uploaded'),
                    message: this.model.get('failureMessage'),
                    actions: {
                        primary: {
                            text: gettext('Close'),
                            click: function(prompt) {
                                return prompt.hide();
                            }
                        }
                    }
                }).show();
            }
        });

        return ActiveSlideUploadView;
    }
);