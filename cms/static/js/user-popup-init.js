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
            const hasPopupContent = popupRoot.children.length > 0;

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
                } else {
                    console.warn('UserPopup component initializer not found. Loading component...');
                }
            }
        });

        // Close popup when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = popupRoot.contains(event.target) || avatarButton.contains(event.target);
            if (!isClickInside && popupRoot.children.length > 0) {
                // Trigger close through the component
                if (window.closeUserPopupComponent) {
                    window.closeUserPopupComponent();
                }
            }
        });

        console.log('User popup initialized successfully');
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
