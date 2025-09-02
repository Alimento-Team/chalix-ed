/**
 * This is a simple component that renders add buttons for all available XBlock template types.
 */
define(['jquery', 'underscore', 'gettext', 'js/views/baseview', 'common/js/components/utils/view_utils',
    'js/views/components/add_xblock_button', 'js/views/components/add_xblock_menu',
    'js/views/components/add_library_content',
    'edx-ui-toolkit/js/utils/html-utils'],
function($, _, gettext, BaseView, ViewUtils, AddXBlockButton, AddXBlockMenu, AddLibraryContent, HtmlUtils) {
    'use strict';

    var AddXBlockComponent = BaseView.extend({
        events: {
            'click .new-component .new-component-type .multiple-templates': 'showComponentTemplates',
            'click .new-component .new-component-type .single-template': 'createNewComponent',
            'click .new-component .cancel-button': 'closeNewComponent',
            'click .new-component-templates .new-component-template .button-component': 'createNewComponent',
            'click .new-component-templates .cancel-button': 'closeNewComponent'
        },

        initialize: function(options) {
            BaseView.prototype.initialize.call(this, options);
            this.template = this.loadTemplate('add-xblock-component');
        },

        render: function() {
            var that;
            if (!this.$el.html()) {
                that = this;
                this.$el.html(HtmlUtils.HTML(this.template({})).toString());
                
                // Check if there's already an online class component in this unit
                var hasOnlineClass = false;
                if (this.options.parentModel && this.options.parentModel.get('child_info') && 
                    this.options.parentModel.get('child_info').children) {
                    hasOnlineClass = _.some(this.options.parentModel.get('child_info').children, function(child) {
                        return child.metadata && child.metadata.chalix_content_type === 'online_class';
                    });
                }
                
                this.collection.each(
                    function(componentModel) {
                        var view, menu;
                        
                        // Skip online_class components if one already exists
                        if (componentModel.type === 'chalix_content_types' && hasOnlineClass) {
                            // Check if this component model contains online_class templates
                            var hasOnlineClassTemplate = _.some(componentModel.templates, function(template) {
                                return template.metadata && template.metadata.chalix_content_type === 'online_class';
                            });
                            if (hasOnlineClassTemplate) {
                                return; // Skip this component type
                            }
                        }

                        view = new AddXBlockButton({model: componentModel});
                        that.$el.find('.new-component-type').append(view.render().el);

                        menu = new AddXBlockMenu({model: componentModel});
                        that.$el.append(menu.render().el);
                    }
                );
            }
        },

        showComponentTemplates: function(event) {
            var type, parentLocator, model, parentBlockType;
            event.preventDefault();
            event.stopPropagation();

            type = $(event.currentTarget).data('type');
            parentLocator = $(event.currentTarget).closest('.xblock[data-usage-id]').data('usage-id');
            parentBlockType  = $(event.currentTarget).parents('.xblock-author_view').last().data('block-type');
            model = this.collection.models.find(function(item) { return item.type === type; }) || {};

            // Check if there's already an online class component in this unit
            var hasOnlineClass = false;
            if (this.options.parentModel && this.options.parentModel.get('child_info') && 
                this.options.parentModel.get('child_info').children) {
                hasOnlineClass = _.some(this.options.parentModel.get('child_info').children, function(child) {
                    return child.metadata && child.metadata.chalix_content_type === 'online_class';
                });
            }
            
            // If this is a chalix_content_types component and we already have an online class, don't show templates
            if (type === 'chalix_content_types' && hasOnlineClass) {
                var hasOnlineClassTemplate = _.some(model.templates, function(template) {
                    return template.metadata && template.metadata.chalix_content_type === 'online_class';
                });
                if (hasOnlineClassTemplate) {
                    return; // Don't show the template menu
                }
            }

            try {
                if (this.options.isIframeEmbed && parentBlockType !== 'split_test') {
                    window.parent.postMessage(
                        {
                            type: 'showComponentTemplates',
                            payload: {
                                type: type,
                                parentLocator: parentLocator,
                                model: {
                                    type: model.type,
                                    display_name: model.display_name,
                                    templates: model.templates,
                                    support_legend: model.support_legend,
                                },
                            }
                        }, document.referrer
                    );
                    return true;
                }
            } catch (e) {
                console.error(e);
            }

            this.$('.new-component').slideUp(250);
            this.$('.new-component-' + type).slideDown(250);
            this.$('.new-component-' + type + ' div').focus();
        },

        closeNewComponent: function(event) {
            var type;
            event.preventDefault();
            event.stopPropagation();
            type = $(event.currentTarget).data('type');
            this.$('.new-component').slideDown(250);
            this.$('.new-component-templates').slideUp(250);
            this.$('ul.new-component-type li button[data-type=' + type + ']').focus();
        },

        createNewComponent: function(event) {
            var self = this,
                $element = $(event.currentTarget),
                saveData = $element.data(),
                oldOffset = ViewUtils.getScrollOffset(this.$el),
                usageId = $element.closest('.xblock[data-usage-id]').data('usage-id');
            event.preventDefault();
            this.closeNewComponent(event);

            // Check if there's already an online class component in this unit
            var hasOnlineClass = false;
            if (this.options.parentModel && this.options.parentModel.get('child_info') && 
                this.options.parentModel.get('child_info').children) {
                hasOnlineClass = _.some(this.options.parentModel.get('child_info').children, function(child) {
                    return child.metadata && child.metadata.chalix_content_type === 'online_class';
                });
            }
            
            // If this is an online class component and we already have one, don't create it
            if (saveData.category === 'online_class' && hasOnlineClass) {
                return; // Don't create the component
            }

            if (saveData.type === 'library_v2') {
                try {
                  if (this.options.isIframeEmbed) {
                    return window.parent.postMessage(
                      {
                        type: 'showSingleComponentPicker',
                        payload: { usageId },
                      }, document.referrer
                    );
                  }
                } catch (e) {
                  console.error(e);
                }

                var modal = new AddLibraryContent();
                modal.showComponentPicker(
                    this.options.libraryContentPickerUrl,
                    function(data) {
                        ViewUtils.runOperationShowingMessage(
                            gettext('Adding'),
                            _.bind(this.options.createComponent, this, data, $element),
                        ).always(function() {
                            // Restore the scroll position of the buttons so that the new
                            // component appears above them.
                            ViewUtils.setScrollOffset(self.$el, oldOffset);
                        });
                    }.bind(this)
                );
            } else {
                ViewUtils.runOperationShowingMessage(
                    gettext('Adding'),
                    _.bind(this.options.createComponent, this, saveData, $element),
                ).always(function() {
                    // Restore the scroll position of the buttons so that the new
                    // component appears above them.
                    ViewUtils.setScrollOffset(self.$el, oldOffset);
                });
            }
        }
    });

    return AddXBlockComponent;
}); // end define();
