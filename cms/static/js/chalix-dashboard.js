/**
 * CMS Dashboard Tab Management
 * Handles tab switching and content loading for the Vietnamese CMS interface
 */

(function() {
    'use strict';

    // Tab data configuration
    const TAB_CONFIG = {
        'statistics': {
            label: 'Thống kê',
            contentTitle: 'Thống kê hệ thống',
            contentDescription: 'Xem các thống kê và báo cáo tổng quan về hệ thống học tập.'
        },
        'create-account': {
            label: 'Quản lý tài khoản cán bộ',
            contentTitle: 'Quản lý tài khoản cán bộ',
            contentDescription: 'Tạo và quản lý tài khoản cán bộ trong hệ thống.'
        },
        'management': {
            label: 'Quản lý nền tảng',
            contentTitle: 'Quản lý nền tảng',
            contentDescription: 'Quản lý các chức năng và cài đặt nền tảng.'
        },
        'learning-management': {
            label: 'Quản lý học tập',
            contentTitle: 'Quản lý học tập',
            contentDescription: 'Quản lý nội dung học tập, khóa học và tài liệu.'
        },
        'approve-requests': {
            label: 'Phê duyệt yêu cầu',
            contentTitle: 'Phê duyệt yêu cầu',
            contentDescription: 'Xem xét và phê duyệt các yêu cầu từ người học.'
        }
    };

    class CMSDashboard {
        constructor() {
            this.currentTab = 'statistics';
            this.tabElements = {};
            this.contentElement = null;
            
            this.init();
        }

        init() {
            this.bindEvents();
            this.initializeTabs();
            this.setActiveTab(this.currentTab);
        }

        bindEvents() {
            // Handle tab clicks
            document.addEventListener('click', (e) => {
                if (e.target.closest('.tab-item')) {
                    const tabItem = e.target.closest('.tab-item');
                    const tabId = tabItem.dataset.tabId;
                    
                    if (tabId) {
                        this.setActiveTab(tabId);
                    }
                }
            });

            // Handle keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (e.target.closest('.cms-tabs')) {
                    this.handleKeyboardNavigation(e);
                }
            });
        }

        initializeTabs() {
            const tabContainer = document.querySelector('.cms-tabs .tab-container');
            const contentContainer = document.querySelector('.tab-content');
            
            if (!tabContainer || !contentContainer) {
                console.error('Required tab elements not found');
                return;
            }

            this.contentElement = contentContainer;

            // Get role-based available tabs
            const roleData = window.CMS_ROLE_DATA || {};
            const availableTabs = roleData.available_tabs || Object.keys(TAB_CONFIG);
            
            console.info('[CMS Dashboard] Available tabs for role:', roleData.user_role, availableTabs);

            // Clear existing tabs and create new ones
            tabContainer.innerHTML = '';
            
            // Only create tabs that are available for the user's role
            availableTabs.forEach((tabId, index) => {
                if (TAB_CONFIG[tabId]) {
                    const config = TAB_CONFIG[tabId];
                    const tabElement = this.createTabElement(tabId, config.label, index === 0);
                    
                    tabContainer.appendChild(tabElement);
                    this.tabElements[tabId] = tabElement;
                }
            });

            // Set default tab to first available tab
            if (availableTabs.length > 0 && !availableTabs.includes(this.currentTab)) {
                this.currentTab = availableTabs[0];
            }
        }

        createTabElement(tabId, label, isActive = false) {
            const tabItem = document.createElement('div');
            tabItem.className = `tab-item ${isActive ? 'active' : ''}`;
            tabItem.dataset.tabId = tabId;
            tabItem.setAttribute('role', 'tab');
            tabItem.setAttribute('aria-selected', isActive ? 'true' : 'false');
            tabItem.setAttribute('tabindex', isActive ? '0' : '-1');

            const tabLabel = document.createElement('span');
            tabLabel.className = 'tab-label';
            tabLabel.textContent = label;

            tabItem.appendChild(tabLabel);
            
            return tabItem;
        }

        setActiveTab(tabId) {
            if (!TAB_CONFIG[tabId]) {
                console.error(`Invalid tab ID: ${tabId}`);
                return;
            }

            // Check if tab is available for the user's role
            const roleData = window.CMS_ROLE_DATA || {};
            const availableTabs = roleData.available_tabs || Object.keys(TAB_CONFIG);
            
            if (!availableTabs.includes(tabId)) {
                console.warn(`Tab ${tabId} not available for user role: ${roleData.user_role}`);
                return;
            }

            // Update tab appearance
            Object.keys(this.tabElements).forEach(id => {
                const tabElement = this.tabElements[id];
                const isActive = id === tabId;
                
                tabElement.classList.toggle('active', isActive);
                tabElement.setAttribute('aria-selected', isActive ? 'true' : 'false');
                tabElement.setAttribute('tabindex', isActive ? '0' : '-1');
            });

            // Update content
            this.updateTabContent(tabId);
            
            // Update current tab
            this.currentTab = tabId;

            // Update URL hash (optional, for deep linking)
            if (window.history && window.history.replaceState) {
                window.history.replaceState(null, null, `#${tabId}`);
            }
        }

        updateTabContent(tabId) {
            const config = TAB_CONFIG[tabId];
            
            if (!this.contentElement) {
                return;
            }
            // Render tab-specific content
                // Prefer module-based tab renderers when present
                const moduleKey = tabId;
                const tabModule = window.CMS_TABS && window.CMS_TABS[moduleKey];
                if (tabModule && typeof tabModule.render === 'function') {
                    tabModule.render(this.contentElement, {
                        contentTitle: config.contentTitle,
                        contentDescription: config.contentDescription
                    });
                } else {
                    // Default placeholder for other tabs
                    this.contentElement.innerHTML = `
                        <div class="tab-content-placeholder">
                            <h2>${config.contentTitle}</h2>
                            <p>${config.contentDescription}</p>
                            <div style="margin-top: 20px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">
                                <p style="margin: 0; color: #6c757d; font-style: italic;">
                                    Nội dung cho tab này sẽ được phát triển trong các bước tiếp theo.
                                </p>
                            </div>
                        </div>
                    `;
                }
        }

        handleKeyboardNavigation(e) {
            const tabItems = Array.from(document.querySelectorAll('.tab-item'));
            const currentIndex = tabItems.findIndex(tab => tab.classList.contains('active'));
            
            let newIndex = currentIndex;
            
            switch(e.key) {
                case 'ArrowLeft':
                    newIndex = currentIndex > 0 ? currentIndex - 1 : tabItems.length - 1;
                    break;
                case 'ArrowRight':
                    newIndex = currentIndex < tabItems.length - 1 ? currentIndex + 1 : 0;
                    break;
                case 'Home':
                    newIndex = 0;
                    break;
                case 'End':
                    newIndex = tabItems.length - 1;
                    break;
                default:
                    return;
            }
            
            e.preventDefault();
            
            const newTabId = tabItems[newIndex].dataset.tabId;
            if (newTabId) {
                this.setActiveTab(newTabId);
                tabItems[newIndex].focus();
            }
        }

        // Public method to switch to a specific tab
        switchToTab(tabId) {
            this.setActiveTab(tabId);
        }

        // Public method to get current tab
        getCurrentTab() {
            return this.currentTab;
        }
    }

    // Initialize when DOM is ready
    function initCMSDashboard() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.cmsDashboard = new CMSDashboard();
            });
        } else {
            window.cmsDashboard = new CMSDashboard();
        }
    }

    // Check for initial hash in URL
    function handleInitialHash() {
        const hash = window.location.hash.substring(1);
        if (hash && TAB_CONFIG[hash]) {
            // Check if tab is available for user's role
            const roleData = window.CMS_ROLE_DATA || {};
            const availableTabs = roleData.available_tabs || Object.keys(TAB_CONFIG);
            
            if (availableTabs.includes(hash)) {
                setTimeout(() => {
                    if (window.cmsDashboard) {
                        window.cmsDashboard.switchToTab(hash);
                    }
                }, 100);
            }
        }
    }

    // Initialize everything
    initCMSDashboard();

    // Do NOT automatically apply the URL hash on initial load — keep the configured default tab.
    // Still listen for later hash changes (back/forward navigation) and apply them when they occur.
    window.addEventListener('hashchange', handleInitialHash);

})();
