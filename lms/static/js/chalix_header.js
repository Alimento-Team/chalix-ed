/**
 * Chalix Header Module JavaScript
 * 
 * This module handles all interactive functionality for the Chalix header:
 * - User dropdown menu
 * - Notification dropdown
 * - Click outside to close
 * - Keyboard navigation
 * - Notification loading and updates
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    selectors: {
      userAvatar: '#chalix-user-avatar',
      userDropdown: '#chalix-user-dropdown',
      notificationIcon: '#chalix-notification-icon',
      notificationDropdown: '#chalix-notification-dropdown',
      notificationList: '#chalix-notification-list',
      notificationCount: '#chalix-notification-count',
      markAllRead: '#chalix-mark-all-read'
    },
    classes: {
      unread: 'unread',
      read: 'read'
    },
    api: {
      notifications: '/api/chalix/user-menu/notifications/',
      unreadCount: '/api/chalix/user-menu/notifications/unread-count/',
      markRead: '/api/chalix/user-menu/notifications/{id}/read/',
      markAllRead: '/api/chalix/user-menu/notifications/mark-all-read/',
      logout: '/api/chalix/user-menu/logout/'
    }
  };

  // State
  let state = {
    notifications: [],
    unreadCount: 0,
    isDropdownOpen: false,
    isNotificationOpen: false
  };

  /**
   * Initialize the Chalix header module
   */
  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', setupEventListeners);
    } else {
      setupEventListeners();
    }
  }

  /**
   * Setup all event listeners
   */
  function setupEventListeners() {
    // User avatar dropdown
    const userAvatar = document.querySelector(CONFIG.selectors.userAvatar);
    if (userAvatar) {
      userAvatar.addEventListener('click', toggleUserDropdown);
      userAvatar.addEventListener('keydown', handleKeyDown);
    }

    // Notification icon
    const notificationIcon = document.querySelector(CONFIG.selectors.notificationIcon);
    if (notificationIcon) {
      notificationIcon.addEventListener('click', toggleNotificationDropdown);
      notificationIcon.addEventListener('keydown', handleKeyDown);
    }

    // Mark all as read button
    const markAllRead = document.querySelector(CONFIG.selectors.markAllRead);
    if (markAllRead) {
      markAllRead.addEventListener('click', handleMarkAllAsRead);
    }

    // Click outside to close dropdowns
    document.addEventListener('click', handleClickOutside);

    // Load initial notification count
    loadUnreadCount();

    // Poll for notification updates every 60 seconds
    setInterval(loadUnreadCount, 60000);
  }

  /**
   * Toggle user dropdown visibility
   */
  function toggleUserDropdown(event) {
    event.stopPropagation();
    
    const dropdown = document.querySelector(CONFIG.selectors.userDropdown);
    const avatar = document.querySelector(CONFIG.selectors.userAvatar);
    
    if (!dropdown || !avatar) return;

    // Close notification dropdown if open
    if (state.isNotificationOpen) {
      closeNotificationDropdown();
    }

    state.isDropdownOpen = !state.isDropdownOpen;
    
    if (state.isDropdownOpen) {
      dropdown.removeAttribute('hidden');
      avatar.setAttribute('aria-expanded', 'true');
    } else {
      dropdown.setAttribute('hidden', '');
      avatar.setAttribute('aria-expanded', 'false');
    }
  }

  /**
   * Toggle notification dropdown visibility
   */
  function toggleNotificationDropdown(event) {
    event.stopPropagation();
    
    const dropdown = document.querySelector(CONFIG.selectors.notificationDropdown);
    const icon = document.querySelector(CONFIG.selectors.notificationIcon);
    
    if (!dropdown || !icon) return;

    // Close user dropdown if open
    if (state.isDropdownOpen) {
      closeUserDropdown();
    }

    state.isNotificationOpen = !state.isNotificationOpen;
    
    if (state.isNotificationOpen) {
      dropdown.removeAttribute('hidden');
      icon.setAttribute('aria-expanded', 'true');
      loadNotifications();
    } else {
      dropdown.setAttribute('hidden', '');
      icon.setAttribute('aria-expanded', 'false');
    }
  }

  /**
   * Close user dropdown
   */
  function closeUserDropdown() {
    const dropdown = document.querySelector(CONFIG.selectors.userDropdown);
    const avatar = document.querySelector(CONFIG.selectors.userAvatar);
    
    if (dropdown && avatar) {
      dropdown.setAttribute('hidden', '');
      avatar.setAttribute('aria-expanded', 'false');
      state.isDropdownOpen = false;
    }
  }

  /**
   * Close notification dropdown
   */
  function closeNotificationDropdown() {
    const dropdown = document.querySelector(CONFIG.selectors.notificationDropdown);
    const icon = document.querySelector(CONFIG.selectors.notificationIcon);
    
    if (dropdown && icon) {
      dropdown.setAttribute('hidden', '');
      icon.setAttribute('aria-expanded', 'false');
      state.isNotificationOpen = false;
    }
  }

  /**
   * Handle click outside dropdowns
   */
  function handleClickOutside(event) {
    const userAvatar = document.querySelector(CONFIG.selectors.userAvatar);
    const userDropdown = document.querySelector(CONFIG.selectors.userDropdown);
    const notificationIcon = document.querySelector(CONFIG.selectors.notificationIcon);
    const notificationDropdown = document.querySelector(CONFIG.selectors.notificationDropdown);

    // Close user dropdown if clicking outside
    if (state.isDropdownOpen && 
        userAvatar && userDropdown &&
        !userAvatar.contains(event.target) && 
        !userDropdown.contains(event.target)) {
      closeUserDropdown();
    }

    // Close notification dropdown if clicking outside
    if (state.isNotificationOpen && 
        notificationIcon && notificationDropdown &&
        !notificationIcon.contains(event.target) && 
        !notificationDropdown.contains(event.target)) {
      closeNotificationDropdown();
    }
  }

  /**
   * Handle keyboard navigation
   */
  function handleKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      event.target.click();
    } else if (event.key === 'Escape') {
      closeUserDropdown();
      closeNotificationDropdown();
    }
  }

  /**
   * Load notifications from API
   */
  function loadNotifications() {
    fetch(CONFIG.api.notifications, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to load notifications');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        state.notifications = data.notifications || [];
        state.unreadCount = data.unread_count || 0;
        renderNotifications();
        updateUnreadCount();
      }
    })
    .catch(error => {
      console.error('Error loading notifications:', error);
      renderNotificationsError();
    });
  }

  /**
   * Load unread count from API
   */
  function loadUnreadCount() {
    fetch(CONFIG.api.unreadCount, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to load unread count');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        state.unreadCount = data.unread_count || 0;
        updateUnreadCount();
      }
    })
    .catch(error => {
      console.error('Error loading unread count:', error);
    });
  }

  /**
   * Update unread count badge
   */
  function updateUnreadCount() {
    const badge = document.querySelector(CONFIG.selectors.notificationCount);
    if (!badge) return;

    if (state.unreadCount > 0) {
      badge.textContent = state.unreadCount > 99 ? '99+' : state.unreadCount;
      badge.removeAttribute('hidden');
    } else {
      badge.setAttribute('hidden', '');
    }
  }

  /**
   * Render notifications in the dropdown
   */
  function renderNotifications() {
    const list = document.querySelector(CONFIG.selectors.notificationList);
    if (!list) return;

    if (state.notifications.length === 0) {
      list.innerHTML = `
        <div class="no-notifications">
          <p>Không có thông báo mới</p>
        </div>
      `;
      return;
    }

    list.innerHTML = state.notifications.map(notification => `
      <div class="notification-item ${notification.is_read ? 'read' : 'unread'}"
           data-notification-id="${notification.id}"
           data-action-url="${notification.action_url || ''}"
           role="button"
           tabindex="0">
        <div class="notification-content">
          <div class="notification-message">${escapeHtml(notification.title)}</div>
          <div class="notification-time">${escapeHtml(notification.time_since_created)}</div>
        </div>
      </div>
    `).join('');

    // Add click handlers to notification items
    list.querySelectorAll('.notification-item').forEach(item => {
      item.addEventListener('click', handleNotificationClick);
      item.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          handleNotificationClick.call(item, event);
        }
      });
    });
  }

  /**
   * Render notifications error state
   */
  function renderNotificationsError() {
    const list = document.querySelector(CONFIG.selectors.notificationList);
    if (!list) return;

    list.innerHTML = `
      <div class="no-notifications">
        <p>Không thể tải thông báo. Vui lòng thử lại sau.</p>
      </div>
    `;
  }

  /**
   * Handle notification item click
   */
  function handleNotificationClick(event) {
    const item = event.currentTarget;
    const notificationId = item.dataset.notificationId;
    const actionUrl = item.dataset.actionUrl;
    const isRead = item.classList.contains('read');

    if (!isRead) {
      markNotificationAsRead(notificationId);
    }

    if (actionUrl) {
      window.location.href = actionUrl;
    }
  }

  /**
   * Mark a notification as read
   */
  function markNotificationAsRead(notificationId) {
    const url = CONFIG.api.markRead.replace('{id}', notificationId);
    
    fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to mark notification as read');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        // Update local state
        const notification = state.notifications.find(n => n.id === parseInt(notificationId));
        if (notification) {
          notification.is_read = true;
        }
        state.unreadCount = Math.max(0, state.unreadCount - 1);
        
        // Update UI
        const item = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
        if (item) {
          item.classList.remove('unread');
          item.classList.add('read');
        }
        updateUnreadCount();
      }
    })
    .catch(error => {
      console.error('Error marking notification as read:', error);
    });
  }

  /**
   * Handle mark all as read
   */
  function handleMarkAllAsRead(event) {
    event.preventDefault();

    fetch(CONFIG.api.markAllRead, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to mark all notifications as read');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        // Update local state
        state.notifications.forEach(notification => {
          notification.is_read = true;
        });
        state.unreadCount = 0;
        
        // Update UI
        document.querySelectorAll('.notification-item.unread').forEach(item => {
          item.classList.remove('unread');
          item.classList.add('read');
        });
        updateUnreadCount();
      }
    })
    .catch(error => {
      console.error('Error marking all notifications as read:', error);
    });
  }

  /**
   * Escape HTML to prevent XSS
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Initialize on load
  init();

  // Expose public API if needed
  window.ChalixHeader = {
    loadNotifications,
    loadUnreadCount,
    closeUserDropdown,
    closeNotificationDropdown
  };

})();
