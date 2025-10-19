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
        // Prefer server-provided LMS base URL from CMS_ROLE_DATA when available. This should come from
        // platform settings (MFE_CONFIG['LMS_BASE_URL'] or LMS_ROOT_URL) so we don't heuristically
        // construct the LMS host on the client.
        let lmsBaseUrl = roleData.lms_base_url || '';
        if (!lmsBaseUrl) {
            // Fallback: determine the LMS base URL by deriving from current location (legacy behavior)
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
            // If no explicit port and hostname is same, don't append port (will use default)
            lmsBaseUrl = protocol + '//' + lmsHost + (lmsPort ? ':' + lmsPort : '');
        }
        
        // Use the current origin's account path as fallback when explicit URLs are not provided
        const originAccountBase = location.origin + '/account/';

        function sameOriginOrFallback(maybeUrl, fallback) {
            if (!maybeUrl) return fallback;
            try {
                const parsed = new URL(maybeUrl, location.href);
                if (parsed.origin === location.origin) return parsed.origin + parsed.pathname.replace(/\/$/, '');
            } catch (e) {
                // ignore invalid URLs
            }
            return fallback;
        }

        // Use CMS-provided URLs directly since they're authoritative from platform config
        const accountBase = roleData.account_settings_url || originAccountBase;
        const profileBase = roleData.profile_base_url || originAccountBase;

        return {
            // LMS dashboard - navigate to LMS
            courses: lmsBaseUrl + '/dashboard',
            // Account settings MFE (link to /account by default)
            account: accountBase,
            // Profile MFE
            profile: profileBase + '/u/' + username,
            // Logout - always use the CMS frontend logout URL so the logout flow runs on
            // the current site (LogoutView -> IDA iframe logout -> redirect).
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
                    <a href="${urls.logout}" style="display: block; padding: 12px 16px; color: #333; text-decoration: none; font-size: 14px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">🚪 Đăng xuất</a>
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
    window.closeUserPopupComponent = function() {
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