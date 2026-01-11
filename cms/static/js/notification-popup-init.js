/**
 * Notification Popup Component Initialization for CMS Header
 * This script initializes the notification popup when the notification bell is clicked.
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    function initNotificationPopup() {
        const notificationButton = document.querySelector('.notification-button');
        const popupRoot = document.getElementById('notification-popup-root');

        if (!notificationButton || !popupRoot) {
            // Required elements not found; skipping initialization
            return;
        }

        // Initialize notification badge
        if (window.initNotificationBadge) {
            window.initNotificationBadge();
        }

        // Handle notification button click
        notificationButton.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            // Check if popup is currently open
            const isExpanded = notificationButton.getAttribute('aria-expanded') === 'true';
            const hasPopupContent = popupRoot.children.length > 0;

            if (isExpanded || hasPopupContent) {
                // Close the popup
                if (window.closeNotificationPopupComponent) {
                    window.closeNotificationPopupComponent();
                }
            } else {
                // Open the popup
                notificationButton.setAttribute('aria-expanded', 'true');
                if (window.initNotificationPopupComponent) {
                    window.initNotificationPopupComponent();
                    
                    // Prevent immediate close by outside click handlers
                    window._notificationPopupJustOpened = true;
                    setTimeout(() => {
                        window._notificationPopupJustOpened = false;
                    }, 300);
                } else {
                    // Notification popup component initializer not found
                }
            }
        });

        // Close popup when clicking outside
        document.addEventListener('click', function(event) {
            // Don't close if popup was just opened
            if (window._notificationPopupJustOpened) {
                return;
            }
            
            const popupElement = document.querySelector('.notification-popup-menu');
            const isClickInside = (popupElement && popupElement.contains(event.target)) || 
                                 popupRoot.contains(event.target) || 
                                 notificationButton.contains(event.target);
            const hasPopup = popupRoot.children.length > 0;
            
            if (!isClickInside && hasPopup) {
                if (window.closeNotificationPopupComponent) {
                    window.closeNotificationPopupComponent();
                }
            }
        });

        // Close on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && popupRoot.children.length > 0) {
                if (window.closeNotificationPopupComponent) {
                    window.closeNotificationPopupComponent();
                }
            }
        });

        // Notification popup initialized (log removed)
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotificationPopup);
    } else {
        initNotificationPopup();
    }

    // Also expose initialization for manual triggering if needed
    window.initNotificationPopupOnDemand = initNotificationPopup;

})();
