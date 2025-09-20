define(
    ['jquery', 'underscore', 'backbone', 'js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils',
        'js/views/previous_slide_upload', 'text!templates/active-slide-upload-list.underscore'],
    function($, _, Backbone, BaseView, HtmlUtils, PreviousSlideUploadView, previousSlideUploadListTemplate) {
        'use strict';

        var PreviousSlideUploadListView = BaseView.extend({
            tagName: 'div',
            className: 'assets-library',

            initialize: function(options) {
                this.template = HtmlUtils.template(previousSlideUploadListTemplate);
                this.slideHandlerUrl = options.slideHandlerUrl;
                this.slideSupportedFileFormats = options.slideSupportedFileFormats;
                this.itemViews = this.collection.map(function(model) {
                    return new PreviousSlideUploadView({
                        slideHandlerUrl: options.slideHandlerUrl,
                        model: model,
                        slideSupportedFileFormats: options.slideSupportedFileFormats
                    });
                });
            },

            render: function() {
                var $el = this.$el,
                    $tabBody;

                HtmlUtils.setHtml(
                    this.$el,
                    this.template({})
                );

                $tabBody = $el.find('.js-table-body');
                _.each(this.itemViews, function(view) {
                    $tabBody.append(view.render().$el);
                });
                return this;
            }
        });

        return PreviousSlideUploadListView;
    }
);