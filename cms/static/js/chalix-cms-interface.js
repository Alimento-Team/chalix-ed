/**
 * Vietnamese CMS Interface JavaScript - Tab Functionality
 * Based on Figma Design Requirements
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeTabs();
        initializeActionButtons();
        loadTabData();
    });

    /**
     * Initialize tab functionality
     */
    function initializeTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanels = document.querySelectorAll('.tab-panel');

        // Set up click handlers for tab buttons
        tabButtons.forEach(function(button, index) {
            button.addEventListener('click', function() {
                activateTab(index);
            });

            // Add keyboard support
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    activateTab(index);
                }
            });
        });

        // Activate first tab by default
        if (tabButtons.length > 0) {
            activateTab(0);
        }
    }

    /**
     * Activate specific tab
     * @param {number} tabIndex - Index of tab to activate
     */
    function activateTab(tabIndex) {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanels = document.querySelectorAll('.tab-panel');

        // Remove active class from all tabs
        tabButtons.forEach(function(button) {
            button.classList.remove('active');
        });

        tabPanels.forEach(function(panel) {
            panel.classList.remove('active');
        });

        // Add active class to selected tab
        if (tabButtons[tabIndex] && tabPanels[tabIndex]) {
            tabButtons[tabIndex].classList.add('active');
            tabPanels[tabIndex].classList.add('active');

            // Update URL hash without scrolling
            const tabId = tabPanels[tabIndex].id;
            if (tabId) {
                history.replaceState(null, null, '#' + tabId);
            }

            // Load specific tab data
            loadTabSpecificData(tabIndex);
        }
    }

    /**
     * Initialize action buttons
     */
    function initializeActionButtons() {
        const actionButtons = document.querySelectorAll('.action-button');
        
        actionButtons.forEach(function(button) {
            // Add click handlers for course creation actions
            button.addEventListener('click', function(e) {
                const action = button.getAttribute('data-action');
                
                if (action) {
                    e.preventDefault();
                    handleActionButtonClick(action, button);
                }
            });

            // Add hover effect enhancement
            button.addEventListener('mouseenter', function() {
                button.style.transform = 'translateY(-3px)';
            });

            button.addEventListener('mouseleave', function() {
                button.style.transform = 'translateY(-2px)';
            });
        });
    }

    /**
     * Handle action button clicks
     * @param {string} action - Action type
     * @param {Element} button - Button element
     */
    function handleActionButtonClick(action, button) {
        // Show loading state
        const originalText = button.querySelector('.button-text').textContent;
        const loadingSpinner = '<span class="loading"></span>';
        
        button.querySelector('.button-text').innerHTML = loadingSpinner + ' Đang xử lý...';
        button.disabled = true;

        // Handle different actions
        switch (action) {
            case 'create-course':
                redirectToCourseCreation();
                break;
            case 'create-program':
                redirectToProgramCreation();
                break;
            case 'create-class':
                redirectToClassCreation();
                break;
            default:
                console.log('Unknown action:', action);
                resetButtonState(button, originalText);
        }
    }

    /**
     * Redirect to course creation
     */
    function redirectToCourseCreation() {
        // Try to find the original course creation URL
        const createCourseLink = document.querySelector('a[href*="course"]');
        if (createCourseLink) {
            window.location.href = createCourseLink.href;
        } else {
            // Fallback to standard course creation path
            window.location.href = '/course/';
        }
    }

    /**
     * Redirect to program creation
     */
    function redirectToProgramCreation() {
        // Handle program creation logic
        console.log('Creating new program...');
        // This would typically open a modal or redirect to program creation page
        alert('Tính năng tạo chương trình học đang được phát triển.');
    }

    /**
     * Redirect to class creation
     */
    function redirectToClassCreation() {
        // Handle class creation logic
        console.log('Creating new class...');
        // This would typically open a modal or redirect to class creation page
        alert('Tính năng tạo lớp học đang được phát triển.');
    }

    /**
     * Reset button state after action
     * @param {Element} button - Button element
     * @param {string} originalText - Original button text
     */
    function resetButtonState(button, originalText) {
        setTimeout(function() {
            button.querySelector('.button-text').textContent = originalText;
            button.disabled = false;
        }, 2000);
    }

    /**
     * Load tab data on initialization
     */
    function loadTabData() {
        // Load statistics for first tab
        loadStatistics();
        
        // Check URL hash and activate corresponding tab
        const hash = window.location.hash.substring(1);
        if (hash) {
            const targetPanel = document.getElementById(hash);
            if (targetPanel) {
                const tabIndex = Array.from(document.querySelectorAll('.tab-panel')).indexOf(targetPanel);
                if (tabIndex !== -1) {
                    activateTab(tabIndex);
                }
            }
        }
    }

    /**
     * Load specific data for each tab
     * @param {number} tabIndex - Index of active tab
     */
    function loadTabSpecificData(tabIndex) {
        switch (tabIndex) {
            case 0: // Thống kê
                loadStatistics();
                break;
            case 1: // Tạo tài khoản cán bộ
                setupUserCreationForm();
                break;
            case 2: // Quản lý
                loadManagementData();
                break;
            case 3: // Nhập tài liệu học tập
                setupDocumentUpload();
                break;
            case 4: // Phê duyệt yêu cầu
                loadApprovalRequests();
                break;
        }
    }

    /**
     * Load statistics data
     */
    function loadStatistics() {
        // This would typically fetch real data from the backend
        const statsData = {
            totalCourses: 127,
            activeLearners: 2843,
            completedCourses: 89,
            newRegistrations: 45
        };

        updateStatCard('total-courses', statsData.totalCourses);
        updateStatCard('active-learners', statsData.activeLearners);
        updateStatCard('completed-courses', statsData.completedCourses);
        updateStatCard('new-registrations', statsData.newRegistrations);
    }

    /**
     * Update stat card with animated counting
     * @param {string} cardId - Card element ID
     * @param {number} targetValue - Target number to display
     */
    function updateStatCard(cardId, targetValue) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const numberElement = card.querySelector('.stat-number');
        if (!numberElement) return;

        animateNumber(numberElement, 0, targetValue, 1500);
    }

    /**
     * Animate number counting effect
     * @param {Element} element - Element to animate
     * @param {number} start - Start value
     * @param {number} end - End value
     * @param {number} duration - Animation duration in ms
     */
    function animateNumber(element, start, end, duration) {
        const startTime = Date.now();
        const difference = end - start;

        function updateNumber() {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.floor(start + (difference * easedProgress));
            
            element.textContent = currentValue.toLocaleString('vi-VN');

            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        }

        updateNumber();
    }

    /**
     * Setup user creation form validation
     */
    function setupUserCreationForm() {
        const form = document.getElementById('user-creation-form');
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic form validation
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('error');
                    isValid = false;
                } else {
                    field.classList.remove('error');
                }
            });

            if (isValid) {
                // Submit form data
                submitUserCreationForm(form);
            } else {
                alert('Vui lòng điền đầy đủ thông tin bắt buộc.');
            }
        });
    }

    /**
     * Submit user creation form
     * @param {Element} form - Form element
     */
    function submitUserCreationForm(form) {
        const submitButton = form.querySelector('.submit-button');
        const originalText = submitButton.textContent;
        
        submitButton.innerHTML = '<span class="loading"></span> Đang tạo tài khoản...';
        submitButton.disabled = true;

        // Simulate API call
        setTimeout(function() {
            alert('Tài khoản đã được tạo thành công!');
            form.reset();
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }, 2000);
    }

    /**
     * Load management data
     */
    function loadManagementData() {
        // This would load course management data, user lists, etc.
        console.log('Loading management data...');
    }

    /**
     * Setup document upload functionality
     */
    function setupDocumentUpload() {
        const uploadArea = document.getElementById('document-upload-area');
        if (!uploadArea) return;

        // Setup drag and drop
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', function() {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            handleFileUpload(files);
        });
    }

    /**
     * Handle file upload
     * @param {FileList} files - Files to upload
     */
    function handleFileUpload(files) {
        Array.from(files).forEach(function(file) {
            console.log('Uploading file:', file.name);
            // Handle file upload logic here
        });
    }

    /**
     * Load approval requests
     */
    function loadApprovalRequests() {
        // This would load pending approval requests
        console.log('Loading approval requests...');
    }

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function() {
        const hash = window.location.hash.substring(1);
        if (hash) {
            const targetPanel = document.getElementById(hash);
            if (targetPanel) {
                const tabIndex = Array.from(document.querySelectorAll('.tab-panel')).indexOf(targetPanel);
                if (tabIndex !== -1) {
                    activateTab(tabIndex);
                }
            }
        }
    });

    // Expose some functions globally for external use
    window.ChalixCMS = {
        activateTab: activateTab,
        loadTabData: loadTabData
    };

})();
