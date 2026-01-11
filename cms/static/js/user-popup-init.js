/**
 * User Popup Component Initialization for CMS Header
 * This script initializes the React UserPopup component when the user avatar is clicked.
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    function initUserPopup() {
        const avatarButton = document.getElementById('user-avatar-popup-trigger');
        const popupRoot = document.getElementById('user-popup-root');

        if (!avatarButton || !popupRoot) {
            console.warn('User popup initialization: Required elements not found');
            return;
        }

        // Try to load and mount the UserPopup component
        // This will be called when the avatar button is clicked
        avatarButton.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            // Check if popup is currently open
            const isExpanded = avatarButton.getAttribute('aria-expanded') === 'true';
            const hasFloating = !!document.getElementById('chalix-user-menu-floating');
            const hasFallback = popupRoot && popupRoot.children.length > 0;
            const hasPopupContent = hasFloating || hasFallback || document.querySelectorAll('.user-popup-fallback').length > 0;

            if (isExpanded || hasPopupContent) {
                // Close the popup
                if (window.closeUserPopupComponent) {
                    window.closeUserPopupComponent();
                }
            } else {
                // Open the popup
                avatarButton.setAttribute('aria-expanded', 'true');
                if (window.initUserPopupComponent) {
                    window.initUserPopupComponent(popupRoot);
                    
                        // Prevent immediate close by outside click handlers or capture-phase listeners
                        // Add a short-lived flag to ignore accidental early closes.
                        window._popupJustOpened = true;
                        // Keep the window slightly longer to account for capture-phase document handlers
                        setTimeout(() => {
                            window._popupJustOpened = false;
                        }, 300);
                        // Also provide a programmatic force-close helper if a later action needs to close immediately
                        window.forceCloseUserPopup = function() {
                            // call close with force=true to bypass the guard
                            if (window.closeUserPopupComponent) {
                                window.closeUserPopupComponent(true);
                            }
                        };
                } else {
                    // UserPopup component initializer not found
                }
            }
        });

        // Close popup when clicking outside
        document.addEventListener('click', function(event) {
            // Don't close if popup was just opened
            if (window._popupJustOpened) {
                return;
            }
            
            const popupElement = document.querySelector('.user-popup-fallback');
            const floatingPopup = document.getElementById('chalix-user-menu-floating');
            const isClickInside = (popupElement && popupElement.contains(event.target)) || 
                                 (floatingPopup && floatingPopup.contains(event.target)) ||
                                 (popupRoot && popupRoot.contains(event.target)) || 
                                 avatarButton.contains(event.target);
            const hasPopup = !!floatingPopup || (popupRoot && popupRoot.children.length > 0) || document.querySelectorAll('.user-popup-fallback').length > 0;
            
            if (!isClickInside && hasPopup) {
                // Trigger close through the component
                if (window.closeUserPopupComponent) {
                    window.closeUserPopupComponent();
                }
            }
        });

        // Close on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const floatingPopup = document.getElementById('chalix-user-menu-floating');
                const hasPopup = !!floatingPopup || (popupRoot && popupRoot.children.length > 0);
                if (hasPopup && window.closeUserPopupComponent) {
                    window.closeUserPopupComponent();
                }
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initUserPopup);
    } else {
        initUserPopup();
    }

    // Also expose initialization for manual triggering if needed
    window.initUserPopupOnDemand = initUserPopup;

})();
