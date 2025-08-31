define([
    'jquery', 'backbone', 'js/views/simplified_course_outline'
], function($, Backbone, SimplifiedCourseOutlineView) {
    'use strict';

    return function(courseInfo, outlineInfo) {
        var courseModel, outlineView;

        // Set up the course model
        courseModel = new Backbone.Model(courseInfo);

        // Set up the simplified outline view
        outlineView = new SimplifiedCourseOutlineView({
            el: $('.simplified-course-outline'),
            model: courseModel,
            initialState: outlineInfo.locator_to_show
        });

        outlineView.render();

        return {
            courseModel: courseModel,
            outlineView: outlineView
        };
    };
});
