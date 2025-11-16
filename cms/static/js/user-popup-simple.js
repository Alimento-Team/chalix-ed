/**
 * Simple User Popup Component for CMS
 * Creates a dropdown popup when user clicks their avatar
 */

(function(global) {
    'use strict';

    /**
     * Get current user info from the page or API
     */
    function getCurrentUserInfo() {
        // Try to get user info from the CMS role data first
        if (window.CMS_ROLE_DATA && window.CMS_ROLE_DATA.user_name) {
            return {
                fullName: window.CMS_ROLE_DATA.user_name,
                role: window.CMS_ROLE_DATA.user_role || 'User'
            };
        }
        
        // Fallback: try to get from Django user context or other global vars
        if (window.user && window.user.username) {
            return {
                fullName: window.user.username,
                role: 'User'
            };
        }
        
        // Last fallback
        return {
            fullName: 'Current User',
            role: 'User'
        };
    }

    /**
     * Get navigation URLs for the popup menu items
     * Construct URLs dynamically using platform settings
     */
    function getNavigationUrls() {
        const roleData = window.CMS_ROLE_DATA || {};
        const username = roleData.user_name || 'user';
        
        // Get MFE URLs from CMS_ROLE_DATA (passed from backend)
        const lmsBaseUrl = roleData.lms_base_url || '';
        const learningBaseUrl = roleData.learning_base_url || lmsBaseUrl;
        const learnerDashboardUrl = roleData.learner_dashboard_url || (lmsBaseUrl + '/dashboard');
        const accountSettingsUrl = roleData.account_settings_url || (lmsBaseUrl + '/account/settings');
        const accountProfileUrl = roleData.account_profile_url || lmsBaseUrl;
        
        // Fallback for older configurations without MFE URLs
        if (!roleData.learning_base_url && !lmsBaseUrl) {
            // Determine the LMS base URL by deriving from current location (legacy behavior)
            const protocol = window.location.protocol; // e.g. 'http:'
            const hostname = window.location.hostname; // e.g. 'studio.local.openedx.io'
            const port = window.location.port; // e.g. '8001'

            // If running on the 'studio.' subdomain in dev, remove the 'studio.' prefix
            let lmsHost = hostname;
            if (hostname.startsWith('studio.')) {
                lmsHost = hostname.replace(/^studio\./, '');
            }

            // Map common dev CMS port to LMS port. If CMS is 8001, LMS commonly runs on 8000.
            let lmsPort = port === '8001' ? '8000' : port;
            const fallbackLmsBaseUrl = protocol + '//' + lmsHost + (lmsPort ? ':' + lmsPort : '');
            
            return {
                courses: fallbackLmsBaseUrl + '/dashboard',
                account: fallbackLmsBaseUrl + '/account/settings',
                profile: fallbackLmsBaseUrl + '/u/' + username,
                logout: '/logout/'
            };
        }

        // Construct profile URL with username
        const profileUrl = accountProfileUrl 
            ? (accountProfileUrl.endsWith('/') ? accountProfileUrl : accountProfileUrl + '/') + 'u/' + username
            : null;

        return {
            // Courses - use learner dashboard MFE
            courses: learnerDashboardUrl,
            // Account settings - use account settings MFE
            account: accountSettingsUrl,
            // Profile - use profile MFE with username
            profile: profileUrl,
            // Logout - always use the CMS frontend logout URL
            logout: '/logout/'
        };
    }

    /**
     * Create the user popup menu
     */
    function createUserPopup() {
        const rootElement = document.getElementById('user-popup-root');
        if (!rootElement) return;

        const userInfo = getCurrentUserInfo();
        const urls = getNavigationUrls();

        const popup = document.createElement('div');
        popup.className = 'user-popup-menu';
        popup.style.cssText = `
            position: absolute;
            top: 60px;
            right: 0;
            width: 280px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-family: 'Inter', sans-serif;
        `;

        popup.innerHTML = `
            <div style="padding: 16px 0;">
                <div style="padding: 0 16px 12px; border-bottom: 1px solid #f0f0f0;">
                    <div style="font-weight: 600; font-size: 16px; color: #333; margin-bottom: 4px;">${userInfo.fullName.toUpperCase()}</div>
                    <div style="font-size: 14px; color: #666;">${userInfo.role}</div>
                </div>
                <div style="padding: 8px 0;">
                    <a href="${urls.courses}" style="display: block; padding: 12px 16px; color: #333; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">📚 Khóa học</a>
                    <a href="${urls.account}" style="display: block; padding: 12px 16px; color: #333; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">📊 Cập nhật thông tin</a>
                    <a href="#" style="display: block; padding: 12px 16px; color: #999; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5; cursor: not-allowed;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">❤️ Danh sách yêu cầu</a>
                    <a href="${urls.profile}" style="display: block; padding: 12px 16px; color: #333; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">📈 Kết quả học tập</a>
                    <a href="#" style="display: block; padding: 12px 16px; color: #999; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5; cursor: not-allowed;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">🎓 Đăng ký giảng dạy</a>
                    <a href="#" style="display: block; padding: 12px 16px; color: #999; text-decoration: none; font-size: 14px; border-bottom: 1px solid #f5f5f5; cursor: not-allowed;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">💡 Trợ giúp</a>
                    <a href="${urls.logout}" style="display: block; padding: 12px 16px; color: #dc3545; text-decoration: none; font-size: 14px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">� Đăng xuất</a>
                </div>
            </div>
        `;

        rootElement.appendChild(popup);
        console.log('User popup menu created successfully');
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
            console.log('closeUserPopupComponent (simple): ignored because popup was just opened');
            return;
        }

        const rootElement = document.getElementById('user-popup-root');
        if (rootElement) {
            rootElement.innerHTML = '';
            
            const trigger = document.getElementById('user-avatar-popup-trigger');
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        }
    };

})(window);