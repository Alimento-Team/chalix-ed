define([
    'jquery', 'underscore', 'backbone',
    'js/views/xblock_outline',
    'js/views/utils/xblock_utils'
], function($, _, Backbone, XBlockOutlineView, XBlockViewUtils) {
    'use strict';

    var SimplifiedCourseOutlineView = XBlockOutlineView.extend({

        events: _.extend({}, XBlockOutlineView.prototype.events, {
            'click .button-new[data-category="vertical"]': 'handleAddEvent'
        }),

        getTemplateContext: function() {
            var xblockInfo = this.model,
                childInfo = xblockInfo.get('child_info'),
                isCollapsed = this.shouldRenderChildren() && !this.shouldExpandChildren();

            return {
                xblockInfo: xblockInfo,
                visibilityClass: XBlockViewUtils.getXBlockVisibilityClass(xblockInfo.get('visibility_state')),
                typeListClass: 'course',
                parentInfo: this.parentInfo,
                xblockType: 'course',
                xblockTypeDisplayName: 'Course',
                parentType: null,
                childType: 'unit',
                childCategory: 'vertical',
                addChildLabel: 'Tạo Chuyên Đề',
                defaultNewChildName: 'Unit',
                isCollapsed: isCollapsed,
                includesChildren: this.shouldRenderChildren(),
                hasExplicitStaffLock: this.model.get('has_explicit_staff_lock'),
                staffOnlyMessage: this.model.get('staff_only_message'),
                hideFromTOCMessage: this.model.get('hide_from_toc_message'),
                enableHideFromTOC: this.model.get('hide_from_toc'),
                course: this.model,
                enableCopyPasteUnits: this.model.get('enable_copy_paste_units'),
                isTaggingFeatureDisabled: this.model.get('is_tagging_feature_disabled')
            };
        },

        handleAddEvent: function(event) {
            var self = this,
                $target = $(event.currentTarget),
                category = 'vertical'; // Always create vertical units in simplified view

            event.preventDefault();
            XBlockViewUtils.addXBlock($target).done(function(locator) {
                self.onChildAdded(locator, category, event);
            });
        },

        onChildAdded: function(locator, category) {
            // For units in simplified view, redirect to the new unit page
            if (category === 'vertical') {
                this.onUnitAdded(locator);
            } else {
                this.refresh();
            }
        },

        onUnitAdded: function(locator) {
            // Redirect to container page for editing the new unit
            window.location.href = '/container/' + locator + '?action=new';
        }

    });

    return SimplifiedCourseOutlineView;
});
