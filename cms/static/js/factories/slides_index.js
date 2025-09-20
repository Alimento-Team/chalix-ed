define([
    'jquery', 'backbone', 'js/views/active_slide_upload_list',
    'js/views/previous_slide_upload_list', 'js/views/active_slide_upload'
], function($, Backbone, ActiveSlideUploadListView, PreviousSlideUploadListView, ActiveSlideUpload) {
    'use strict';

    var SlidesIndexFactory = function(
        $contentWrapper,
        slideHandlerUrl,
        previousUploads,
        slideSupportedFileFormats,
        slideUploadMaxFileSize
    ) {
        var activeView = new ActiveSlideUploadListView({
                postUrl: slideHandlerUrl,
                slideSupportedFileFormats: slideSupportedFileFormats,
                slideUploadMaxFileSize: slideUploadMaxFileSize,
                onFileUploadDone: function(activeSlides) {
                    $.ajax({
                        url: slideHandlerUrl,
                        contentType: 'application/json',
                        dataType: 'json',
                        type: 'GET'
                    }).done(function(responseData) {
                        var updatedCollection = new Backbone.Collection(responseData.slides || []).filter(function(slide) {
                                // Include slides that are not in the active slide upload list,
                                // or that are marked as Upload Complete
                                var isActive = activeSlides.where({slideId: slide.get('slide_id')});
                                return isActive.length === 0
                                       || isActive[0].get('status') === ActiveSlideUpload.STATUS_COMPLETE;
                            }),
                            updatedView = new PreviousSlideUploadListView({
                                slideHandlerUrl: slideHandlerUrl,
                                collection: updatedCollection,
                                slideSupportedFileFormats: slideSupportedFileFormats
                            });
                        $contentWrapper.find('.assets-library').replaceWith(updatedView.render().$el);
                    });
                }
            }),
            previousView = new PreviousSlideUploadListView({
                slideHandlerUrl: slideHandlerUrl,
                collection: new Backbone.Collection(previousUploads),
                slideSupportedFileFormats: slideSupportedFileFormats
            });

        // Create wrapper for assets
        var $assetsWrapper = $('<div class="wrapper-assets"></div>');
        $assetsWrapper.append(previousView.render().$el);
        $contentWrapper.append(activeView.render().$el);
        $contentWrapper.append($assetsWrapper);
    };

    return SlidesIndexFactory;
});