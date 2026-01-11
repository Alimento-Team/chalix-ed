/**
 * Simple User Popup Component for CMS - Matching MFE Header Design
 * Creates a dark dropdown popup when user clicks their avatar
 */

(function(global) {
    'use strict';

    /**
     * Get current user info from the page or API
     */
    function getCurrentUserInfo() {
        // Try to get user info from the CMS role data first
        if (window.CMS_ROLE_DATA) {
            return {
                fullName: window.CMS_ROLE_DATA.user_name || 'Current User',
                username: window.CMS_ROLE_DATA.username || '',
                organization: window.CMS_ROLE_DATA.organization_name || '',
                role: window.CMS_ROLE_DATA.user_role || ''
            };
        }
        
        // Fallback: try to get from Django user context or other global vars
        if (window.user && window.user.username) {
            return {
                fullName: window.user.username,
                username: window.user.username,
                organization: '',
                role: ''
            };
        }
        
        // Last fallback
        return {
            fullName: 'Current User',
            username: '',
            organization: '',
            role: ''
        };
    }

    /**
     * Get navigation URLs for the popup menu items
     */
    function getNavigationUrls() {
        const roleData = window.CMS_ROLE_DATA || {};
        const username = roleData.username || roleData.user_name || 'user';
        
        // Get MFE URLs from CMS_ROLE_DATA (passed from backend)
        const lmsBaseUrl = roleData.lms_base_url || '';
        const learnerDashboardUrl = roleData.learner_dashboard_url || (lmsBaseUrl + '/dashboard');
        const accountSettingsUrl = roleData.account_settings_url || (lmsBaseUrl + '/account/settings');
        const accountProfileUrl = roleData.account_profile_url || lmsBaseUrl;
        
        // Construct profile URL with username
        const profileUrl = accountProfileUrl 
            ? (accountProfileUrl.endsWith('/') ? accountProfileUrl : accountProfileUrl + '/') + 'u/' + username
            : lmsBaseUrl + '/u/' + username;
        
        // Personalization URL (learner dashboard with personalized tab)
        const personalizationUrl = learnerDashboardUrl && learnerDashboardUrl.includes('?')
            ? learnerDashboardUrl + '&tab=personalized'
            : learnerDashboardUrl + '?tab=personalized';

        return {
            courses: learnerDashboardUrl,
            account: accountSettingsUrl,
            personalization: personalizationUrl,
            requests: lmsBaseUrl + '/requests',
            profile: profileUrl,
            teaching: '#', // TODO: Add teaching registration URL
            help: '#', // TODO: Add help URL
            logout: '/logout'
        };
    }

    /**
     * Create the user popup menu matching MFE header design
     */
    function createUserPopup() {
        // Create a floating popup appended to document.body and position it under the visible avatar button
        const avatarButton = document.getElementById('user-avatar-popup-trigger');
        if (!avatarButton) return;

        const userInfo = getCurrentUserInfo();
        const urls = getNavigationUrls();

        // Remove any existing floating popup
        const prev = document.getElementById('chalix-user-menu-floating');
        if (prev && prev.parentNode) {
            prev.parentNode.removeChild(prev);
        }

        const popup = document.createElement('div');
        popup.id = 'chalix-user-menu-floating';
        popup.className = 'chalix-user-menu';
        popup.style.position = 'absolute';
        popup.style.visibility = 'hidden';

        // metadata
        const metaParts = [];
        if (userInfo.username) { metaParts.push('<span class="chalix-user-menu__username">@' + userInfo.username + '</span>'); }
        if (userInfo.organization) { if (metaParts.length > 0) { metaParts.push('<span class="chalix-user-menu__dot">•</span>'); } metaParts.push('<span class="chalix-user-menu__org">' + userInfo.organization + '</span>'); }
        const metaHtml = metaParts.length > 0 ? metaParts.join('') : '';

        popup.innerHTML =
            '<div class="chalix-user-menu__header">' +
                '<div class="chalix-user-menu__avatar" aria-hidden="true">' +
                    '<i class="fa fa-user"></i>' +
                '</div>' +
                '<div class="chalix-user-menu__info">' +
                    '<div class="chalix-user-menu__name">' + userInfo.fullName + '</div>' +
                    (metaHtml ? '<div class="chalix-user-menu__meta">' + metaHtml + '</div>' : '') +
                '</div>' +
            '</div>' +
            '<nav class="chalix-user-menu__list">' +
                '<a class="chalix-user-menu__item" href="' + urls.courses + '">' +
                    '<i class="fa fa-book"></i>' +
                    '<span>Khóa học</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.account + '">' +
                    '<i class="fa fa-user"></i>' +
                    '<span>Cập nhật thông tin</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.personalization + '">' +
                    '<i class="fa fa-sliders"></i>' +
                    '<span>Cá nhân hóa</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.requests + '">' +
                    '<i class="fa fa-list-alt"></i>' +
                    '<span>Danh sách yêu cầu</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.profile + '">' +
                    '<i class="fa fa-bar-chart"></i>' +
                    '<span>Kết quả học tập</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.teaching + '">' +
                    '<i class="fa fa-chalkboard-teacher"></i>' +
                    '<span>Đăng ký giảng dạy</span>' +
                '</a>' +
                '<a class="chalix-user-menu__item" href="' + urls.help + '">' +
                    '<i class="fa fa-question-circle"></i>' +
                    '<span>Trợ giúp</span>' +
                '</a>' +
            '</nav>' +
            '<div class="chalix-user-menu__footer">' +
                '<a class="chalix-user-menu__logout" href="' + urls.logout + '">' +
                    '<i class="fa fa-sign-out"></i>' +
                    '<span>Đăng xuất</span>' +
                '</a>' +
            '</div>';

        document.body.appendChild(popup);

        function positionPopup() {
            const rect = avatarButton.getBoundingClientRect();
            // position popup top just below the avatar button
            const top = window.pageYOffset + rect.bottom + 8;
            popup.style.top = top + 'px';
            // right-align to avatar right edge, with small margin
            const right = Math.max(8, Math.round(window.innerWidth - (rect.right)));
            popup.style.right = right + 'px';
            popup.style.visibility = 'visible';
        }

        // initial position after render
        setTimeout(positionPopup, 10);

        // update on scroll/resize
        const repositionHandler = function() { positionPopup(); };
        window.addEventListener('resize', repositionHandler);
        window.addEventListener('scroll', repositionHandler, { passive: true });

        // store handler for cleanup
        popup._chalix_reposition = repositionHandler;
    }

    /**
     * Public interface for initializing the popup
     */
    window.initUserPopupComponent = function() {
        createUserPopup();
    };

    /**
     * Close the UserPopup component
     */
    window.closeUserPopupComponent = function(force) {
        // Prevent early closure if popup was just opened unless forced
        if (window._popupJustOpened && !force) {
            // ignored because popup was just opened
            return;
        }

        // Remove floating popup if present
        const popup = document.getElementById('chalix-user-menu-floating');
        if (popup) {
            // remove event handlers
            if (popup._chalix_reposition) {
                window.removeEventListener('resize', popup._chalix_reposition);
                window.removeEventListener('scroll', popup._chalix_reposition);
            }
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }

        // Also clear any server-side root fallback element
        const rootElement = document.getElementById('user-popup-root');
        if (rootElement) {
            rootElement.innerHTML = '';
        }

        const trigger = document.getElementById('user-avatar-popup-trigger');
        if (trigger) {
            trigger.setAttribute('aria-expanded', 'false');
        }
    };

})(window);
