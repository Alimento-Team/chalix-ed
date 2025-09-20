define([
    'jquery',
    'underscore',
    'backbone',
    'js/models/active_slide_upload',
    'js/views/baseview',
    'js/views/active_slide_upload',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/active-slide-upload-list.underscore',
    'jquery.fileupload'
],
function($, _, Backbone, ActiveSlideUpload, BaseView, ActiveSlideUploadView,
    HtmlUtils, StringUtils, activeSlideUploadListTemplate) {
    'use strict';

    var ActiveSlideUploadListView,
        CONVERSION_FACTOR_MBS_TO_BYTES = 1000 * 1000;

    ActiveSlideUploadListView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .file-drop-area': 'chooseFile',
            'dragleave .file-drop-area': 'dragleave',
            'drop .file-drop-area': 'dragleave'
        },

        uploadHeader: gettext('Upload Slides'),
        uploadText: HtmlUtils.interpolateHtml(
            gettext('Drag and drop or {spanStart}browse your computer{spanEnd}.'),
            {
                spanStart: HtmlUtils.HTML('<span class="upload-text-link">'),
                spanEnd: HtmlUtils.HTML('</span>')
            }
        ),
        defaultFailureMessage: gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.'),

        initialize: function(options) {
            this.template = HtmlUtils.template(activeSlideUploadListTemplate);
            this.collection = new Backbone.Collection();
            this.itemViews = [];
            this.listenTo(this.collection, 'add', this.addUpload);
            this.postUrl = options.postUrl;
            this.slideSupportedFileFormats = options.slideSupportedFileFormats;
            this.slideUploadMaxFileSize = options.slideUploadMaxFileSize;
            this.onFileUploadDone = options.onFileUploadDone;

            this.maxSizeText = StringUtils.interpolate(
                gettext('Maximum file size: {maxFileSize} MB'),
                {
                    maxFileSize: this.slideUploadMaxFileSize
                }
            );
            this.supportedSlidesText = StringUtils.interpolate(
                gettext('Supported file types: {supportedSlideTypes}'),
                {
                    supportedSlideTypes: Object.keys(this.slideSupportedFileFormats).join(', ')
                }
            );
        },

        render: function() {
            var context = {
                uploadHeader: this.uploadHeader,
                uploadText: this.uploadText,
                maxSizeText: this.maxSizeText,
                supportedSlidesText: this.supportedSlidesText
            };
            HtmlUtils.setHtml(this.$el, this.template(context));
            this.$('.file-input').fileupload({
                dataType: 'json',
                type: 'POST',
                singleFileUploads: false,
                sequentialUploads: true,
                limitConcurrentUploads: 1,
                url: this.postUrl,
                dropZone: this.$('.file-drop-area'),
                pasteZone: null,
                formData: function(form) {
                    return [];
                },
                add: this.addFile.bind(this),
                progress: this.progress.bind(this),
                done: this.done.bind(this),
                fail: this.fail.bind(this)
            });
            return this;
        },

        addFile: function(e, data) {
            var file = data.files[0],
                fileName = file.name,
                fileSize = file.size,
                maxSize = this.slideUploadMaxFileSize * CONVERSION_FACTOR_MBS_TO_BYTES;

            if (fileSize > maxSize) {
                this.showError(gettext('File size exceeds maximum allowed size.'));
                return;
            }

            var slideUpload = new ActiveSlideUpload({
                slideId: 'slide-' + Date.now(),
                fileName: fileName,
                status: ActiveSlideUpload.STATUS_UPLOADING,
                progress: 0
            });

            this.collection.add(slideUpload);
            data.slideUpload = slideUpload;
            data.submit();
        },

        progress: function(e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            data.slideUpload.set('progress', progress);
        },

        done: function(e, data) {
            var response = data.result;
            data.slideUpload.set({
                status: ActiveSlideUpload.STATUS_COMPLETED,
                progress: 100
            });
            if (this.onFileUploadDone) {
                this.onFileUploadDone(this.collection);
            }
        },

        fail: function(e, data) {
            data.slideUpload.set({
                status: ActiveSlideUpload.STATUS_FAILED,
                failureMessage: this.defaultFailureMessage
            });
        },

        addUpload: function(model) {
            var view = new ActiveSlideUploadView({model: model});
            this.itemViews.push(view);
            this.$('.active-slide-upload-list').append(view.render().$el);
        },

        chooseFile: function() {
            this.$('.file-input').click();
        },

        dragleave: function() {
            // Handle drag and drop events
        },

        showError: function(message) {
            // Show error message to user
            console.error(message);
        }
    });

    return ActiveSlideUploadListView;
});