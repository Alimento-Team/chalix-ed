define(
    ['backbone', 'gettext'],
    function(Backbone, gettext) {
        'use strict';

        var statusStrings = {
            // Translators: This is the status of a slide upload that is queued
            // waiting for other uploads to complete
            STATUS_QUEUED: gettext('Queued'),
            // Translators: This is the status of an active slide upload
            STATUS_UPLOADING: gettext('Uploading'),
            // Translators: This is the status of a slide upload that has
            // completed successfully
            STATUS_COMPLETED: gettext('Upload completed'),
            // Translators: This is the status of a slide upload that has failed
            STATUS_FAILED: gettext('Upload failed')
        };

        var ActiveSlideUpload = Backbone.Model.extend(
            {
                defaults: {
                    slideId: null,
                    fileName: '',
                    status: statusStrings.STATUS_QUEUED,
                    progress: 0,
                    failureMessage: null
                },

                uploading: function() {
                    var status = this.get('status');
                    return (this.get('progress') < 1) && ((status === statusStrings.STATUS_UPLOADING));
                }
            },
            statusStrings
        );

        return ActiveSlideUpload;
    }
);