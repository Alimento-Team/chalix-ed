/**
 * Simple Notification Popup Component for CMS
 * Creates a dropdown notification panel when user clicks the bell icon
 */

(function(global) {
    'use strict';

    /**
     * Format relative time in Vietnamese
     */
    function formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return diffMins + ' phút trước';
        if (diffHours < 24) return diffHours + ' giờ trước';
        if (diffDays === 1) return '1 ngày trước';
        if (diffDays < 7) return diffDays + ' ngày trước';
        
        // Format as date for older notifications
        return date.toLocaleDateString('vi-VN');
    }

    /**
     * Fetch notifications from API
     */
    function fetchNotifications() {
        // TODO: Implement actual API call to fetch notifications
        // Example: return fetch('/api/notifications/v1/notifications/', {
        //     credentials: 'include',
        //     headers: { 'Accept': 'application/json' }
        // }).then(response => response.json()).then(data => data.results || []);
        
        // Return empty array until API is implemented
        return Promise.resolve([]);
    }

    /**
     * Create a notification item element
     */
    function createNotificationItem(notification) {
        const isUnread = !notification.last_read;
        const item = document.createElement('div');
        item.className = 'notification-item' + (isUnread ? ' notification-item--unread' : '');
        item.style.cssText = `
            display: flex;
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
            transition: background-color 0.2s;
        `;

        item.innerHTML = `
            <div style="width: 8px; flex-shrink: 0; padding-top: 6px; margin-right: 8px;">
                ${isUnread ? '<div style="width: 6px; height: 6px; background: #0066cc; border-radius: 50%;"></div>' : ''}
            </div>
            <div style="flex: 1;">
                <div style="font-size: 14px; color: #333; line-height: 1.5; margin-bottom: 4px;">${notification.content}</div>
                <div style="font-size: 12px; color: #666;">${formatTimeAgo(notification.created)}</div>
            </div>
        `;

        // Add hover effect
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });

        // Add click handler
        if (notification.content_url) {
            item.addEventListener('click', function() {
                window.location.href = notification.content_url;
            });
        }

        return item;
    }

    /**
     * Create the notification popup
     */
    function createNotificationPopup() {
        const rootElement = document.getElementById('notification-popup-root');
        if (!rootElement) {
            console.warn('Notification popup root element not found');
            return;
        }

        const popup = document.createElement('div');
        popup.className = 'notification-popup-menu';
        popup.style.cssText = `
            position: absolute;
            top: 60px;
            right: 50px;
            width: 400px;
            max-width: 90vw;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-family: 'Inter', sans-serif;
            max-height: 600px;
            display: flex;
            flex-direction: column;
        `;

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            padding: 16px;
            border-bottom: 1px solid #e0e0e0;
            background: #f8f9fa;
            border-radius: 8px 8px 0 0;
        `;
        header.innerHTML = '<h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #333;">THÔNG BÁO</h3>';
        popup.appendChild(header);

        // Body (scrollable notification list)
        const body = document.createElement('div');
        body.className = 'notification-popup-body';
        body.style.cssText = `
            flex: 1;
            overflow-y: auto;
            max-height: 450px;
        `;

        // Loading state
        body.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;"><i class="fa fa-spinner fa-spin" style="font-size: 24px;"></i><div style="margin-top: 12px;">Đang tải...</div></div>';
        popup.appendChild(body);

        rootElement.appendChild(popup);

        // Fetch and display notifications
        fetchNotifications().then(function(notifications) {
            if (notifications.length === 0) {
                body.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;">Không có thông báo mới</div>';
            } else {
                body.innerHTML = '';
                notifications.forEach(function(notification) {
                    body.appendChild(createNotificationItem(notification));
                });

                // Footer with "View All" button
                const footer = document.createElement('div');
                footer.style.cssText = `
                    padding: 12px 16px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    background: #f8f9fa;
                    border-radius: 0 0 8px 8px;
                `;
                footer.innerHTML = '<button style="background: none; border: none; color: #0066cc; font-size: 14px; font-weight: 500; cursor: pointer; padding: 8px 16px;" onmouseover="this.style.textDecoration=\'underline\'" onmouseout="this.style.textDecoration=\'none\'">Xem tất cả thông báo</button>';
                
                footer.querySelector('button').addEventListener('click', function() {
                    window.location.href = '/notifications';
                });

                popup.appendChild(footer);
            }
        }).catch(function(error) {
            console.error('Error fetching notifications:', error);
            body.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">Không thể tải thông báo</div>';
        });

        // Notification popup created (log removed)
    }

    /**
     * Get unread notification count
     */
    function getUnreadCount() {
        return fetchNotifications().then(function(notifications) {
            return notifications.filter(function(n) { return !n.last_read; }).length;
        });
    }

    /**
     * Update notification badge
     */
    function updateNotificationBadge() {
        const button = document.querySelector('.notification-button');
        if (!button) return;

        getUnreadCount().then(function(count) {
            let badge = button.querySelector('.notification-badge');
            
            if (count > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'notification-badge';
                    badge.style.cssText = `
                        position: absolute;
                        top: -4px;
                        right: -4px;
                        background: #dc3545;
                        color: white;
                        border-radius: 10px;
                        padding: 2px 6px;
                        font-size: 11px;
                        font-weight: 600;
                        min-width: 18px;
                        text-align: center;
                    `;
                    button.style.position = 'relative';
                    button.appendChild(badge);
                }
                badge.textContent = count > 99 ? '99+' : count;
            } else if (badge) {
                badge.remove();
            }
        });
    }

    /**
     * Public interface for initializing the notification popup
     */
    window.initNotificationPopupComponent = function() {
        createNotificationPopup();
    };

    /**
     * Close the notification popup component
     */
    window.closeNotificationPopupComponent = function(force) {
        // Prevent early closure if popup was just opened unless forced
        if (window._notificationPopupJustOpened && !force) {
            // closeNotificationPopupComponent ignored because popup was just opened (log removed)
            return;
        }

        const rootElement = document.getElementById('notification-popup-root');
        if (rootElement) {
            rootElement.innerHTML = '';
            
            const trigger = document.querySelector('.notification-button');
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        }
    };

    /**
     * Initialize notification badge on page load
     */
    window.initNotificationBadge = function() {
        updateNotificationBadge();
        // Update badge every 60 seconds
        setInterval(updateNotificationBadge, 60000);
    };

})(window);
