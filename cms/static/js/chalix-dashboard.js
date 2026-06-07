/**
 * CMS Dashboard Tab Management
 * Handles tab switching and content loading for the Vietnamese CMS interface
 * Note: Tabs are rendered server-side for security. This script only handles interactions.
 */

(function() {
    'use strict';

    // Tab data configuration (for content only - tabs are rendered server-side)
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
            label: 'Quản lý cơ quan',
            contentTitle: 'Quản lý cơ quan',
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
            this.currentTab = null;
            this.tabElements = {};
            this.contentElement = null;
            
            this.init();
        }

        init() {
            this.initializeTabs();
            this.bindEvents();
            
            // Set initial tab from URL hash or first available
            const hashTab = window.location.hash.replace('#', '');
            const firstTab = Object.keys(this.tabElements)[0];
            const initialTab = (hashTab && this.tabElements[hashTab]) ? hashTab : firstTab;
            
            if (initialTab) {
                this.setActiveTab(initialTab);
            }
        }

        bindEvents() {
            // Handle tab clicks using event delegation
            document.addEventListener('click', (e) => {
                const tabButton = e.target.closest('.cms-tab');
                if (tabButton) {
                    const tabId = tabButton.dataset.tab;
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
            // Tabs are rendered server-side - just find them in the DOM
            const tabButtons = document.querySelectorAll('.cms-tab[data-tab]');
            const contentContainer = document.querySelector('.tab-content');
            
            if (!contentContainer) {
                console.error('[CMS Dashboard] Content container not found');
                return;
            }

            this.contentElement = contentContainer;

            // Build tab elements map from server-rendered tabs
            tabButtons.forEach(tabButton => {
                const tabId = tabButton.dataset.tab;
                if (tabId) {
                    this.tabElements[tabId] = tabButton;
                }
            });

            const availableTabIds = Object.keys(this.tabElements);
            console.info('[CMS Dashboard] Server-rendered tabs:', availableTabIds);
        }

        setActiveTab(tabId) {
            // Verify tab exists in DOM (server-rendered)
            if (!this.tabElements[tabId]) {
                console.warn(`[CMS Dashboard] Tab ${tabId} not found in DOM`);
                return;
            }

            // Update tab appearance
            Object.keys(this.tabElements).forEach(id => {
                const tabElement = this.tabElements[id];
                const isActive = id === tabId;
                
                tabElement.classList.toggle('active', isActive);
                tabElement.classList.toggle('selected', isActive);
                tabElement.setAttribute('aria-selected', isActive ? 'true' : 'false');
            });

            // Update content
            this.updateTabContent(tabId);
            
            // Update current tab
            this.currentTab = tabId;

            // Update URL hash for deep linking
            if (window.history && window.history.replaceState) {
                window.history.replaceState(null, null, `#${tabId}`);
            }
        }

        updateTabContent(tabId) {
            const config = TAB_CONFIG[tabId];
            
            if (!this.contentElement) {
                return;
            }
            
            // Check if tab has its own module renderer
            const tabModule = window.CMS_TABS && window.CMS_TABS[tabId];
            
            if (tabModule && typeof tabModule.render === 'function') {
                // Let the module handle everything including data fetching
                tabModule.render(this.contentElement, {
                    contentTitle: config.contentTitle,
                    contentDescription: config.contentDescription
                });
                return;
            }
            
            // For tabs without modules, fetch data from dashboard_api
            this.fetchTabData(tabId).then(tabData => {
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
            }).catch(error => {
                console.error('Error fetching tab data:', error);
                // Show placeholder on error
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
            });
        }

        async fetchTabData(tabId) {
            try {
                const response = await fetch(`/dashboard_api?tab=${tabId}`, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    return data;
                }
                
                return null;
            } catch (error) {
                console.error('Error fetching tab data:', error);
                return null;
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
