/**
 * React User Popup Component Loader for CMS
 * This script handles loading and mounting the UserPopup React component
 * from the Chalix MFE into the CMS header.
 */

(function(global) {
    'use strict';

    // Configuration
    const config = {
        // Do NOT default to localhost:1997 here. Prefer a data-attribute or global var.
        mfeBaseUrl: null,
        apiBaseUrl: '/api/user/v1',
        componentRoot: 'user-popup-root',
        containerClass: 'user-popup-container'
    };

    /**
     * Load the UserPopup component bundle from the MFE
     */
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.type = 'text/javascript';
            script.async = true;

            script.onload = function() {
                console.log('UserPopup bundle loaded successfully from', src);
                resolve(src);
            };

            script.onerror = function() {
                console.warn('Failed to load UserPopup bundle from:', src);
                // remove the failed script node to keep DOM clean
                if (script.parentNode) script.parentNode.removeChild(script);
                reject(new Error('Failed to load script: ' + src));
            };

            document.head.appendChild(script);
        });
    }

    function loadUserPopupBundle() {
        // Build the candidate list and try sequentially until one succeeds
        return new Promise((resolve, reject) => {
            const rootEl = document.getElementById(config.componentRoot);
            const dataUrl = rootEl && rootEl.getAttribute('data-mfe-base-url');
            const globalUrl = (typeof window !== 'undefined' && window.CHALIX_MFE_COMPONENT_HEADER_URL) ? window.CHALIX_MFE_COMPONENT_HEADER_URL : null;
            const resolvedBase = (dataUrl && dataUrl.trim()) || (globalUrl && globalUrl.trim()) || '';

            const candidates = [];

            if (resolvedBase) {
                const base = resolvedBase.replace(/\/$/, '');
                // Try a few plausible locations on the dev MFE host
                candidates.push(base + '/user-popup-bundle.js');
                candidates.push(base + '/static/js/user-popup-bundle.js');
            }

            // If the platform injected CMS_ROLE_DATA with an mfe_base_url, use that for loading bundles
            try {
                if (window.CMS_ROLE_DATA && window.CMS_ROLE_DATA.mfe_base_url) {
                    const mfeBase = String(window.CMS_ROLE_DATA.mfe_base_url).replace(/\/$/, '');
                    if (mfeBase) {
                        candidates.push(mfeBase + '/user-popup-bundle.js');
                        candidates.push(mfeBase + '/static/js/user-popup-bundle.js');
                    }
                }
                // Fallback: try to extract MFE base from account_settings_url
                else if (window.CMS_ROLE_DATA && window.CMS_ROLE_DATA.account_settings_url) {
                    const acctUrl = String(window.CMS_ROLE_DATA.account_settings_url);
                    // Strip /account/ path to get the MFE base URL for loading bundles
                    const mfeBase = acctUrl.replace(/\/account\/?$/, '').replace(/\/$/, '');
                    if (mfeBase && mfeBase !== acctUrl.replace(/\/$/, '')) {
                        candidates.push(mfeBase + '/user-popup-bundle.js');
                        candidates.push(mfeBase + '/static/js/user-popup-bundle.js');
                    }
                }
            } catch (e) {
                // ignore any odd global values
            }

            // Also try loading the bundle from the common /account public path on this origin
            candidates.push(location.origin + '/account/user-popup-bundle.js');
            candidates.push(location.origin + '/account/static/js/user-popup-bundle.js');

            // Always include same-origin static bundle as a reliable fallback
            candidates.push(location.origin + '/static/js/user-popup-bundle.js');

            console.info('UserPopup: attempting to load bundle from candidates:', candidates);

            // sequentially attempt each candidate
            (function tryNext(index) {
                if (index >= candidates.length) {
                    const err = new Error('All bundle load attempts failed');
                    err.attempted = candidates.slice();
                    return reject(err);
                }

                const src = candidates[index];
                loadScript(src)
                    .then(() => resolve())
                    .catch(() => {
                        // try the next one
                        tryNext(index + 1);
                    });
            })(0);
        });
    }

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
        // Prefer server-provided LMS base URL from CMS_ROLE_DATA when available.
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
        
        // Fallback to the current origin's account path when explicit URLs are not provided
        const originAccountBase = location.origin + '/account/';

        // Use CMS-provided URLs directly since they're authoritative from platform config
        // The account_settings_url should point directly to the account page
        let accountBase = roleData.account_settings_url || (originAccountBase);
        
        // Check if the accountBase already includes /account/ path, if not append it
        if (accountBase && !accountBase.includes('/account')) {
            // Remove trailing slash, append /account/, then add trailing slash
            accountBase = accountBase.replace(/\/+$/, '') + '/account/';
        } else if (typeof accountBase === 'string' && !accountBase.endsWith('/')) {
            // Just ensure trailing slash if /account is already present
            accountBase = accountBase + '/';
        }

        // For profile, extract MFE base URL from account_settings_url if available
        let profileBase = roleData.profile_base_url;
        if (!profileBase && roleData.account_settings_url) {
            // Extract MFE base from account URL and use it for profile
            const mfeBase = roleData.account_settings_url.replace(/\/account\/?$/, '');
            if (mfeBase && mfeBase !== roleData.account_settings_url.replace(/\/$/, '')) {
                profileBase = mfeBase;
            }
        }
        if (!profileBase) {
            profileBase = originAccountBase.replace(/\/account\/?$/, '');
        }
        if (typeof profileBase === 'string' && profileBase.endsWith('/')) {
            // remove trailing slash for consistent concatenation below
            profileBase = profileBase.replace(/\/+$/, '');
        }

        return {
            // LMS dashboard - navigate to LMS
            courses: lmsBaseUrl + '/dashboard',
            // Account settings MFE (point to account root by default, ensure trailing slash)
            account: accountBase,
            // Profile MFE (profileBase + /u/<username>)
            profile: profileBase + '/u/' + username,
            // Logout - always use the CMS frontend logout URL so the logout flow runs on
            // the current site (LogoutView -> IDA iframe logout -> redirect).
            logout: '/logout/'
        };
    }

    /**
     * Create a simple fallback popup when MFE bundle is not available
     */
    function createFallbackPopup() {
        const rootElement = document.getElementById(config.componentRoot);
        if (!rootElement) return;

        const userInfo = getCurrentUserInfo();
        const urls = getNavigationUrls();
        
        // Debug logging to see what URLs we're getting
        console.log('Fallback popup URLs:', urls);
        console.log('CMS_ROLE_DATA.account_settings_url:', window.CMS_ROLE_DATA?.account_settings_url);

        // Get the button position to position the popup correctly
        const triggerButton = document.getElementById('user-avatar-popup-trigger');
        const buttonRect = triggerButton ? triggerButton.getBoundingClientRect() : null;
        
        const popup = document.createElement('div');
        popup.className = 'user-popup-fallback';
        
        // Use fixed positioning to ensure visibility
        const popupStyle = buttonRect ? `
            position: fixed;
            top: ${buttonRect.bottom + 5}px;
            right: ${window.innerWidth - buttonRect.right}px;
            width: 280px;
            max-width: 90vw;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 99999;
            font-family: 'Inter', sans-serif;
            display: block;
            visibility: visible;
            opacity: 1;
            pointer-events: auto;
        ` : `
            position: absolute;
            top: 45px;
            right: 0;
            width: 280px;
            max-width: 90vw;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 99999;
            font-family: 'Inter', sans-serif;
            display: block;
            visibility: visible;
            opacity: 1;
            pointer-events: auto;
        `;
        
        popup.style.cssText = popupStyle;

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

        // Always append to body for fixed positioning
        document.body.appendChild(popup);
        
        // (Removed debug mutation observer and noisy logs)
        
        console.log('Fallback UserPopup created successfully');
        
        // Force a reflow to ensure the popup is rendered
        popup.offsetHeight;
    }

    /**
     * Initialize the UserPopup component with React
     */
    function initializeUserPopupComponent() {
        const rootElement = document.getElementById(config.componentRoot);
        
        if (!rootElement) {
            console.warn('UserPopup root element not found');
            return;
        }

        // Check if React and ReactDOM are available
        if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {
            console.warn('React or ReactDOM not found globally, using fallback');
            createFallbackPopup();
            return;
        }

        // Check if UserPopup component is available from the MFE
        if (typeof window.UserPopupComponent === 'undefined') {
            console.warn('UserPopup component not available from MFE, using fallback');
            createFallbackPopup();
            return;
        }

        try {
            // Create and render the component
            const componentProps = {
                apiBaseUrl: config.apiBaseUrl,
                onClose: function() {
                    // Unmount component
                    ReactDOM.unmountComponentAtNode(rootElement);
                    document.getElementById('user-avatar-popup-trigger').setAttribute('aria-expanded', 'false');
                }
            };

            const element = React.createElement(window.UserPopupComponent, componentProps);
            ReactDOM.render(element, rootElement);
            
            console.log('UserPopup component initialized successfully');
        } catch (error) {
            console.error('Error initializing UserPopup component:', error);
            createFallbackPopup();
        }
    }

    /**
     * Fetch user data from the API
     */
    function fetchUserData() {
        return fetch(config.apiBaseUrl + '/current_user/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]')?.value || ''
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error fetching user data:', error);
            return null;
        });
    }

    /**
     * Public interface for initializing the popup
     */
    window.initUserPopupComponent = function(containerElement) {
        // Skip bundle loading and go directly to fallback popup
        // The MFE React bundle approach isn't set up, so use the simple HTML popup
        console.log('Using fallback popup directly (MFE React bundle not configured)');
        createFallbackPopup();
        
        // Comment out bundle loading to avoid 404 errors:
        // loadUserPopupBundle()
        //     .then(() => initializeUserPopupComponent())
        //     .catch(error => {
        //         console.warn('MFE bundle not available, using fallback popup:', error);
        //         createFallbackPopup();
        //     });
    };

    /**
     * Close the UserPopup component
     */
    window.closeUserPopupComponent = function(force) {
        // If the popup was just opened, ignore accidental/early close calls unless explicitly forced.
        if (window._popupJustOpened && !force) {
            console.log('closeUserPopupComponent: ignored because popup was just opened');
            return;
        }

        const rootElement = document.getElementById(config.componentRoot);
        if (rootElement) {
            // Try React unmount first
            if (typeof ReactDOM !== 'undefined') {
                ReactDOM.unmountComponentAtNode(rootElement);
            }
            // Clear any HTML content (fallback popup)
            rootElement.innerHTML = '';
            
            // Also remove any popup attached to body
            const bodyPopups = document.querySelectorAll('.user-popup-fallback');
            bodyPopups.forEach(popup => popup.remove());
            
            // Clear the dataset flag
            delete rootElement.dataset.popupAttached;
            
            const trigger = document.getElementById('user-avatar-popup-trigger');
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        }
    };

    /**
     * Fetch and return current user data
     */
    window.getUserPopupData = fetchUserData;

})(window);
