/**
 * Vietnamese CMS Interface JavaScript - Tab Functionality
 * Based on Figma Design Requirements
 */

(function() {
    'use strict';
    // Lightweight version marker and early boot log to help browser verification
    const CHALIX_CMS_INTERFACE_VERSION = 'v2.3.1'; // Added evaluation section debugging
    try {
        // Boot logging removed in production
        // Try to inject styles early (ensureProgramModalStyles is a hoisted function)
        if (typeof ensureProgramModalStyles === 'function') {
            try { ensureProgramModalStyles(); /* early style injection succeeded */ } catch (e) { /* early style injection failed */ }
        } else {
            /* ensureProgramModalStyles not yet available at boot */
        }
        // Expose version for quick checks
        window.ChalixCMS_interface_version = CHALIX_CMS_INTERFACE_VERSION;
    } catch (e) {
        /* boot logging suppressed */
    }

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        // Initializing (logs suppressed)
        // Tab initialization is now handled by chalix-dashboard.js
        initializeActionButtons();
        loadTabData();

        // Canonical Figma-accurate modal styles (single consolidated function)
        function ensureProgramModalStyles() {
        if (document.getElementById('chalix-program-modal-styles')) return;
        const css = `
            /* Consolidated Chalix modal styles - high specificity to avoid theme overrides */
            body .chalix-modal-overlay, body .chalix-program-modal-overlay {
                position: fixed !important;
                inset: 0 !important;
                background: rgba(0,0,0,0.45) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 2147483647 !important;
                opacity: 0 !important;
                transition: opacity 200ms ease-in-out !important;
            }

            body .chalix-modal-overlay.show, body .chalix-program-modal-overlay.show { opacity: 1 !important; }

            body .chalix-modal, body .chalix-program-modal {
                width: 640px !important;
                max-width: calc(100% - 64px) !important;
                background: #ffffff !important;
                border-radius: 8px !important;
                box-shadow: 0 12px 30px rgba(11,22,33,0.25) !important;
                position: relative !important;
                overflow: hidden !important;
                transform: translateY(-8px) scale(0.995) !important;
                transition: transform 220ms ease, opacity 180ms ease !important;
                font-family: 'Inter', sans-serif !important;
                box-sizing: border-box !important;
            }

            body .chalix-modal-overlay.show .chalix-modal, body .chalix-program-modal-overlay.show .chalix-program-modal { transform: translateY(0) scale(1) !important; }

            body .chalix-modal-header { padding: 22px 28px 18px 28px !important; position: relative !important; }
            body .chalix-modal-title { margin:0 !important; font-weight:600 !important; font-size:18px !important; letter-spacing:0.3px !important; color:#111827 !important; }

            body .chalix-modal-close, body .modal-close { position:absolute !important; right:18px !important; top:16px !important; width:34px !important; height:34px !important; border-radius:6px !important; background:transparent !important; border:1px solid rgba(17,24,39,0.08) !important; color:#111827 !important; font-size:18px !important; display:flex !important; align-items:center !important; justify-content:center !important; cursor:pointer !important; }

            body .chalix-modal-content { padding:18px 32px 24px 32px !important; }
            body .chalix-form-item { display:flex !important; align-items:center !important; gap:18px !important; margin-bottom:14px !important; }
            body .chalix-form-item label { width:130px !important; color:#374151 !important; font-size:14px !important; }

            body .chalix-input-title { flex:1 !important; height:44px !important; background:#f3f4f6 !important; border:none !important; border-radius:6px !important; padding:10px 14px !important; font-size:13px !important; color:#111827 !important; }

            body .chalix-icon-selector { display:flex !important; align-items:center !important; gap:12px !important; }
            body .chalix-icon-preview { width:52px !important; height:52px !important; border-radius:8px !important; display:flex !important; align-items:center !important; justify-content:center !important; background:#f3f4f6 !important; border:1px solid rgba(17,24,39,0.04) !important; font-size:22px !important; }

            body .chalix-switch-field { display:flex !important; align-items:center !important; gap:12px !important; }
            body .chalix-switch-input { display:none !important; }
            body .chalix-switch-slider { width:44px !important; height:26px !important; border-radius:20px !important; background:#e6eef6 !important; position:relative !important; cursor:pointer !important; }
            body .chalix-switch-slider::after { content:'' !important; width:20px !important; height:20px !important; background:#fff !important; border-radius:50% !important; position:absolute !important; left:3px !important; top:3px !important; transition:transform .18s ease !important; box-shadow:0 2px 6px rgba(16,24,40,0.08) !important; } 
            body .chalix-switch-input:checked + .chalix-switch-slider { background:#29a3ff !important; }
            body .chalix-switch-input:checked + .chalix-switch-slider::after { transform: translateX(18px) !important; }

            /* Topics: ensure they flow normally inside modal */
            body .chalix-topics-section { margin-top:12px !important; padding: 0 !important; }
            body .chalix-topics-list { display:flex !important; flex-direction:column !important; gap:10px !important; }
            body .chalix-topic-item { background:#f3f4f6 !important; border-radius:6px !important; padding:12px 14px !important; display:flex !important; align-items:center !important; justify-content:space-between !important; }
            body .chalix-topic-text { font-size:14px !important; color:#111827 !important; }

            /* Evaluation format section */
            body .chalix-evaluation-section { 
                margin-top:24px !important; 
                padding: 0 !important; 
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
            body .chalix-evaluation-title { 
                font-size:16px !important; 
                font-weight:500 !important; 
                color:#111827 !important; 
                margin:0 0 16px 0 !important;
                display: block !important;
            }
            body .chalix-evaluation-options { 
                display:flex !important; 
                flex-direction:column !important; 
                gap:16px !important;
                visibility: visible !important;
            }
            body .chalix-evaluation-options .evaluation-option { 
                margin-bottom:0 !important;
                display: flex !important;
            }
            body .chalix-evaluation-options .chalix-switch-label { 
                width:auto !important; 
                min-width:200px !important;
                display: block !important;
            }

            body .chalix-add-topic-btn, body .add-topic-button { display:block !important; margin:18px 0 !important; background:#10b981 !important; color:#fff !important; border:none !important; padding:12px 22px !important; border-radius:6px !important; font-weight:600 !important; font-size:14px !important; cursor:pointer !important; }

            body .chalix-modal-buttons { display:flex !important; justify-content:flex-end !important; gap:12px !important; padding:16px 32px 24px 32px !important; }
            body .chalix-btn-cancel { background:#fff !important; border:1px solid #60a5d9 !important; color:#2563eb !important; padding:10px 20px !important; border-radius:6px !important; cursor:pointer !important; }
            body .chalix-btn-submit { background:#1e90ff !important; border:none !important; color:#fff !important; padding:10px 20px !important; border-radius:6px !important; cursor:pointer !important; }

            /* Ensure modal scrolls internally and not on body */
            body .chalix-program-modal, body .chalix-modal { overflow-y: auto !important; max-height: calc(100vh - 96px) !important; }
        `;

        const s = document.createElement('style');
        s.id = 'chalix-program-modal-styles';
        s.appendChild(document.createTextNode(css));
        document.head.appendChild(s);
    }

    /**
     * Redirect to library creation
     */
    function redirectToLibraryCreation() {
        // Try to find the original library creation URL
        const createLibraryLink = document.querySelector('a[href*="library"]');
        if (createLibraryLink) {
            window.location.href = createLibraryLink.href;
        } else {
            // Fallback to standard library creation path
            window.location.href = '/library/';
        }
    }

    /**
     * Redirect to program creation
     */
    function redirectToProgramCreation() {
        // This function is no longer used - program creation now opens modal directly
        openCreateProgramModalDirectly();
    }



    // End consolidated styles (removed duplicate/legacy style blocks)

    // Duplicate module block removed: single canonical module retained above

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
        // Initializing action buttons (log removed)
        
        // Only initialize basic action buttons, don't patch create-program buttons aggressively
        const actionButtons = document.querySelectorAll('.action-button');
        
        // Don't run aggressive patching by default - let tabs handle their own buttons
        // The openCreateProgramModalDirectly function is still available for tabs that want to use it

        actionButtons.forEach(function(button) {
            // Add click handlers for course creation actions
            button.addEventListener('click', function(e) {
                // If this is the create-program button, let the above handler run only
                if (button.getAttribute('data-action') === 'create-program') return;
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                const action = button.getAttribute('data-action');
                if (action) {
                    handleActionButtonClick(action, button);
                } else {
                    if (button.classList.contains('new-course-button')) {
                        handleActionButtonClick('create-course', button);
                    }
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
        // Handle different actions
        switch (action) {
            case 'create-course':
                // Show loading state briefly
                showLoadingState(button, 'Đang chuyển hướng...');
                redirectToCourseCreation();
                break;
            case 'create-program':
                // Directly open modal without loading state to avoid conflicts
                openCreateProgramModalDirectly();
                break;
            case 'create-library':
                // Show loading state briefly
                showLoadingState(button, 'Đang tạo thư viện...');
                redirectToLibraryCreation();
                break;
            case 'create-class':
                // Show loading state briefly
                showLoadingState(button, 'Đang xử lý...');
                redirectToClassCreation();
                break;
            default:
                // Unknown action (log removed)
        }
    }

    /**
     * Show loading state for button
     * @param {Element} button - Button element
     * @param {string} text - Loading text
     */
    function showLoadingState(button, text) {
        const originalText = button.querySelector('.button-text').textContent;
        const loadingSpinner = '<span class="loading"></span>';
        
        button.querySelector('.button-text').innerHTML = loadingSpinner + ' ' + text;
        button.disabled = true;

        // Reset after a short delay
        setTimeout(() => {
            resetButtonState(button, originalText);
        }, 2000);
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
     * Redirect to library creation
     */
    function redirectToLibraryCreation() {
        // Try to find the original library creation URL
        const createLibraryLink = document.querySelector('a[href*="library"]');
        if (createLibraryLink) {
            window.location.href = createLibraryLink.href;
        } else {
            // Fallback to standard library creation path
            window.location.href = '/library/';
        }
    }

    /**
     * Redirect to program creation
     */
    function redirectToProgramCreation() {
        // This function is no longer used - program creation now opens modal directly
        openCreateProgramModalDirectly();
    }

    /**
     * Open program creation modal directly
     */
    function openCreateProgramModalDirectly() {
        // Ensure styles are loaded
        ensureProgramModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'chalix-modal-overlay';
        
        // Create modal with restored chalix-modal structure
        // Creating program modal (log removed)
        
        // Create the modal in parts to avoid any truncation issues
        const modalHTML = [
            '<div class="chalix-modal">',
            '<div class="chalix-modal-header">',
            '<h2 class="chalix-modal-title">TẠO CHƯƠNG TRÌNH HỌC</h2>',
            '<button class="chalix-modal-close" aria-label="Close">×</button>',
            '</div>',
            '<div class="chalix-modal-content">',
            '<div class="chalix-form-item title-field">',
            '<label>Tiêu đề</label>',
            '<input type="text" name="title" class="chalix-input-title" placeholder="Tiêu đề chương trình" />',
            '</div>',
            '<div class="chalix-form-item icon-field">',
            '<label>Biểu tượng</label>',
            '<div class="chalix-icon-selector">',
            '<div class="chalix-icon-grid">',
            '<div class="chalix-icon-option selected" data-icon="🌱"><div class="chalix-icon-preview">🌱</div></div>',
            '<div class="chalix-icon-option" data-icon="📚"><div class="chalix-icon-preview">📚</div></div>',
            '<div class="chalix-icon-option" data-icon="🎓"><div class="chalix-icon-preview">🎓</div></div>',
            '<div class="chalix-icon-option" data-icon="📜"><div class="chalix-icon-preview">📜</div></div>',
            '<div class="chalix-icon-option" data-icon="💡"><div class="chalix-icon-preview">💡</div></div>',
            '<div class="chalix-icon-option" data-icon="🎯"><div class="chalix-icon-preview">🎯</div></div>',
            '</div></div></div>',
            '<div class="chalix-switch-field">',
            '<label class="chalix-switch-label" for="update-topics">Cập nhật các chuyên đề</label>',
            '<div class="chalix-switch-container">',
            '<input type="checkbox" id="update-topics" name="update_topics" class="chalix-switch-input" />',
            '<label for="update-topics" class="chalix-switch-slider"></label>',
            '</div></div>',
            '<div class="chalix-topics-section">',
            '<h4 class="chalix-topics-title">Thêm chuyên đề</h4>',
            '<div class="chalix-topics-list">',
            '<div class="chalix-topic-item">',
            '<span class="chalix-topic-text">Tổng quan về đơn vị sự nghiệp công lập</span>',
            '<button type="button" class="chalix-topic-remove">×</button>',
            '</div></div>',
            '<button type="button" class="chalix-add-topic-btn">+ Thêm mới</button>',
            '</div>'
        ].join('');
        
        // Add the evaluation section separately to ensure it's included
        const evaluationHTML = [
            '<div class="chalix-evaluation-section" style="display: block !important; margin: 20px 0 !important; padding: 16px !important; border: 2px solid #10b981 !important; border-radius: 8px !important; background: #f0fdf4 !important;">',
            '<h4 class="chalix-evaluation-title" style="display: block !important; margin: 0 0 16px 0 !important; font-size: 16px !important; font-weight: 500 !important; color: #111827 !important;">Hình thức kiểm tra cuối khoá</h4>',
            '<div class="chalix-evaluation-options" style="display: flex !important; flex-direction: column !important; gap: 12px !important;">',
            '<div class="chalix-switch-field evaluation-option" style="display: flex !important; align-items: center !important; gap: 12px !important;">',
            '<label class="chalix-switch-label" for="practical-submission" style="min-width: 200px !important; font-size: 14px !important; color: #374151 !important;">Nộp bài thu hoạch</label>',
            '<div class="chalix-switch-container">',
            '<input type="checkbox" id="practical-submission" name="allow_practical_submission" class="chalix-switch-input" checked />',
            '<label for="practical-submission" class="chalix-switch-slider"></label>',
            '</div></div>',
            '<div class="chalix-switch-field evaluation-option" style="display: flex !important; align-items: center !important; gap: 12px !important;">',
            '<label class="chalix-switch-label" for="multiple-choice" style="min-width: 200px !important; font-size: 14px !important; color: #374151 !important;">Làm bài trắc nghiệm</label>',
            '<div class="chalix-switch-container">',
            '<input type="checkbox" id="multiple-choice" name="allow_multiple_choice" class="chalix-switch-input" />',
            '<label for="multiple-choice" class="chalix-switch-slider"></label>',
            '</div></div></div></div>'
        ].join('');
        
        const footerHTML = [
            '</div>',
            '<div class="chalix-modal-buttons">',
            '<button class="chalix-btn-cancel">Hủy</button>',
            '<button class="chalix-btn-submit">Tạo chương trình học</button>',
            '</div></div>'
        ].join('');
        
        overlay.innerHTML = modalHTML + evaluationHTML + footerHTML;
        // Modal HTML set (log removed)

        document.body.appendChild(overlay);

        // Debug: Check if evaluation section exists
        const evaluationSection = overlay.querySelector('.chalix-evaluation-section');
        const evaluationTitle = overlay.querySelector('.chalix-evaluation-title');
        const evaluationOptions = overlay.querySelector('.chalix-evaluation-options');
        const allSections = overlay.querySelectorAll('.chalix-modal-content > *');
        
        // Modal content debug logs removed
        
        if (evaluationSection) {
            // Evaluation section present - debug logging removed
        }

        // Show modal with animation
        requestAnimationFrame(() => overlay.classList.add('show'));

        const closeModal = () => {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 300);
        };

        // Event handlers with correct class names
        overlay.querySelector('.chalix-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.chalix-btn-cancel').addEventListener('click', closeModal);

        // Icon selection functionality
        const iconOptions = overlay.querySelectorAll('.chalix-icon-option');
        iconOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Remove selected class from all options
                iconOptions.forEach(opt => opt.classList.remove('selected'));
                // Add selected class to clicked option
                option.classList.add('selected');
            });
        });

        // Switch functionality for all switches (including evaluation options)
        const switchSliders = overlay.querySelectorAll('.chalix-switch-slider');
        switchSliders.forEach(slider => {
            slider.addEventListener('click', () => {
                const input = slider.previousElementSibling;
                if (input && input.type === 'checkbox') {
                    input.checked = !input.checked;
                }
            });
        });

        // Topic removal
        overlay.addEventListener('click', (e) => {
            if (e.target.classList.contains('chalix-topic-remove')) {
                e.target.closest('.chalix-topic-item').remove();
            }
        });

        // Add topic functionality (inline input instead of prompt)
        const addTopicBtn = overlay.querySelector('.chalix-add-topic-btn');
        const topicsSection = overlay.querySelector('.chalix-topics-section');
        
        addTopicBtn.addEventListener('click', () => {
            // Prevent multiple input rows
            if (topicsSection.querySelector('.chalix-topic-input-row')) return;

            // Hide the add button while editing
            addTopicBtn.style.display = 'none';

            // Create input field container using existing CSS classes
            const inputContainer = document.createElement('div');
            inputContainer.className = 'chalix-topic-input-container';
            inputContainer.innerHTML = `
                <div class="chalix-topic-input-row">
                    <input type="text" class="chalix-topic-input" placeholder="Nhập tên chuyên đề..." maxlength="200" />
                    <div class="chalix-topic-input-actions">
                        <button type="button" class="chalix-topic-save" title="Lưu">✓</button>
                        <button type="button" class="chalix-topic-cancel" title="Hủy">✕</button>
                    </div>
                </div>
            `;

            // Insert the input row before the add button
            topicsSection.insertBefore(inputContainer, addTopicBtn);

            const input = inputContainer.querySelector('.chalix-topic-input');
            const saveBtn = inputContainer.querySelector('.chalix-topic-save');
            const cancelBtn = inputContainer.querySelector('.chalix-topic-cancel');

            input.focus();

            const cleanup = () => {
                inputContainer.remove();
                addTopicBtn.style.display = 'block';
            };

            const saveTopic = () => {
                const topicText = input.value.trim();
                if (topicText) {
                    const topicItem = document.createElement('div');
                    topicItem.className = 'chalix-topic-item';
                    topicItem.innerHTML = `
                        <span class="chalix-topic-text">${escapeHtml(topicText)}</span>
                        <button type="button" class="chalix-topic-remove">
                            <img src="http://localhost:3000/api/figma/images/7b1d96bb0b8a4c5bb29c69bb9c7ab5c993be64fe" alt="Remove" />
                        </button>
                    `;

                    // Append to the topics list container so flow and spacing are consistent
                    const topicsList = topicsSection.querySelector('.chalix-topics-list') || topicsSection;
                    topicsList.appendChild(topicItem);
                }

                cleanup();
            };

            saveBtn.addEventListener('click', saveTopic);
            cancelBtn.addEventListener('click', cleanup);

            // Keyboard: Enter to save, Escape to cancel
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveTopic();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    cleanup();
                }
            });
        });

        // Form submission
        overlay.querySelector('.chalix-btn-submit').addEventListener('click', (e) => {
            const title = overlay.querySelector('.chalix-input-title').value.trim();
            const updateTopics = overlay.querySelector('#update-topics').checked;
            const selectedIcon = overlay.querySelector('.chalix-icon-option.selected')?.dataset.icon || '🌱';
            
            // Collect topics
            const topics = Array.from(topicsSection.querySelectorAll('.chalix-topic-text'))
                .map(el => el.textContent.trim())
                .filter(text => text.length > 0);

            // Collect evaluation format options
            const allowPracticalSubmission = overlay.querySelector('#practical-submission').checked;
            const allowMultipleChoice = overlay.querySelector('#multiple-choice').checked;

            if (!title) {
                alert('Vui lòng nhập tiêu đề chương trình học.');
                return;
            }

            // Show loading state on button
            const submitButton = overlay.querySelector('.chalix-btn-submit');
            showLoadingState(submitButton, 'Đang tạo chương trình học...');

            // POST to backend API
            const url = '/api/chalix/dashboard/create-program/';
            const csrftoken = getCookie('csrftoken');

            fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    title: title, 
                    icon: selectedIcon,
                    update_topics: updateTopics,
                    topics: topics,
                    allow_practical_submission: allowPracticalSubmission,
                    allow_multiple_choice: allowMultipleChoice
                })
            }).then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            }).then(data => {
                    alert('Chương trình học đã được tạo thành công!');
                    closeModal();
                    // Optionally, refresh the program list or take other actions
            }).catch(err => {
                err.text && err.text().then(t => { 
                    let errorMsg = 'Lỗi khi tạo chương trình học';
                    try {
                        const errorData = JSON.parse(t);
                        errorMsg = errorData.error || errorMsg;
                    } catch (e) {
                        // Keep default message
                    }
                    alert(errorMsg); 
                }).catch(() => { 
                    alert('Lỗi khi tạo chương trình học'); 
                });
            });
        });
    }

    // Duplicate function removed - using the corrected version above

    function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function escapeHtml(str){ 
        return String(str).replace(/[&<>"'`]/g, function(s){
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;","`":"&#x60;"}[s]; 
        }); 
    }

    /**
     * Redirect to class creation
     */
    function redirectToClassCreation() {
        // Handle class creation logic
        // (log removed)
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

        // Render program list into a placeholder element (used after creating a program)
        function renderProgramListInPlaceholder(placeholder) {
            if (!placeholder) return;
            const listContainerId = 'lm-program-list';
            let listContainer = placeholder.querySelector('#' + listContainerId);
            if (!listContainer) {
                listContainer = document.createElement('div');
                listContainer.id = listContainerId;
                listContainer.style.textAlign = 'left';
                listContainer.innerHTML = '<div style="color:#546470">Đang tải danh sách chương trình học...</div>';
                placeholder.innerHTML = '<h3 style="margin:0 0 8px;">Danh sách chương trình học</h3>';
                placeholder.appendChild(listContainer);
            }

            fetch('/api/chalix/dashboard/list-programs/', { credentials: 'same-origin', headers: { 'Accept': 'application/json' }})
                .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
                .then(data => {
                    const programs = data.programs || [];
                    if (programs.length === 0) {
                        listContainer.innerHTML = '<div style="color:#546470">Chưa có chương trình học nào.</div>';
                        return;
                    }
                    const html = ['<ul style="list-style:none;padding:0;margin:0">'];
                    for (const p of programs) {
                        const topicsList = (p.topics || []).map(t => escapeHtml(t.title)).join(', ');
                        html.push(`<li style="padding:10px 0;border-bottom:1px solid #eef6fa">
                            <strong>${escapeHtml(p.title)}</strong>
                            <div style="color:#6b7680;font-size:13px;margin:4px 0">${escapeHtml(p.icon || '')} • ${p.update_topics ? 'Tự động cập nhật' : 'Cố định'}</div>
                            <div style="color:#6b7680;font-size:13px;margin:4px 0"><strong>Chuyên đề:</strong> ${topicsList || 'Không có'}</div>
                            <div style="color:#94a3ad;font-size:12px;margin-top:6px">ID: ${p.id} • ${((p.topics&&p.topics.length)||0)} chuyên đề • Tạo bởi: ${escapeHtml(p.created_by || '—')} • ${new Date(p.created_at).toLocaleString()}</div>
                        </li>`);
                    }
                    html.push('</ul>');
                    listContainer.innerHTML = html.join('');
                }).catch(() => {
                    listContainer.innerHTML = '<div style="color:#c23">Lỗi khi tải danh sách chương trình học.</div>';
                });
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
        
        // Initialize process flows after loading statistics
        initializeProcessFlows();
    }
    
    /**
     * Initialize process flows layout
     */
    function initializeProcessFlows() {
        // Initializing process flows (debug logs removed)
        const processContainer = document.querySelector('.process-container');
        if (!processContainer) {
            // No process container found
            return;
        }
        
        // Force re-layout
        processContainer.style.display = 'none';
        processContainer.offsetHeight; // Force reflow
        processContainer.style.display = 'flex';
        
        // Add debug class for testing
        processContainer.classList.add('debug-initialized');
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
        // Load management content in the proper tab panel, not at the bottom
        const managementContainer = document.getElementById('learning-management-container');
        if (managementContainer && window.CMS_TABS && window.CMS_TABS['learning-management']) {
            // Render learning management content in the tab panel only
            window.CMS_TABS['learning-management'].render(managementContainer, {
                contentTitle: 'Quản lý khóa học',
                contentDescription: 'Tạo và quản lý các chương trình học và khóa học'
            });
        }
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
            // Uploading file: debug log removed
            // Handle file upload logic here
        });
    }

    /**
     * Load approval requests
     */
    function loadApprovalRequests() {
        // This would load pending approval requests
        // debug log removed
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

    // Final Evaluation Management Functions
    function openFinalEvaluationModal(courseKey) {
        ensureFinalEvaluationModalStyles();
        
        // Get evaluation data
        fetch(`/api/chalix/evaluation/get/${courseKey}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showFinalEvaluationModal(data, courseKey);
                } else {
                    console.error('Error loading evaluation:', data.error);
                    alert('Không thể tải thông tin kiểm tra cuối khóa');
                }
            })
            .catch(error => {
                console.error('Error loading evaluation:', error);
                alert('Lỗi khi tải thông tin kiểm tra cuối khóa');
            });
    }

    function showFinalEvaluationModal(evaluationData, courseKey) {
        const practical = evaluationData.practical_evaluation;
        const quiz = evaluationData.quiz_evaluation;
        
        const modalHTML = `
            <div id="finalEvaluationModal" class="final-evaluation-modal">
                <div class="final-evaluation-modal-content">
                    <div class="final-evaluation-modal-header">
                        <h2>Quản lý Kiểm tra cuối khóa</h2>
                        <button class="final-evaluation-close-btn">&times;</button>
                    </div>
                    <div class="final-evaluation-modal-body">
                        <div class="evaluation-info">
                            <p><strong>Chương trình:</strong> ${(practical && practical.program_title) || (quiz && quiz.program_title) || 'Không xác định'}</p>
                            <div class="evaluation-types">
                                ${evaluationData.has_practical ? '<span class="eval-type-badge practical">Nộp bài thu hoạch</span>' : ''}
                                ${evaluationData.has_quiz ? '<span class="eval-type-badge quiz">Làm bài trắc nghiệm</span>' : ''}
                            </div>
                        </div>
                        
                        ${evaluationData.has_practical ? `
                            <div class="practical-section evaluation-section">
                                <h3>📝 Câu hỏi thực hành (Nộp bài thu hoạch)</h3>
                                <textarea id="practicalQuestion" class="practical-question-input" 
                                         placeholder="Nhập câu hỏi hoặc hướng dẫn cho bài thực hành...">${practical.practical_question || ''}</textarea>
                                <button id="savePracticalQuestion" class="save-practical-btn">Lưu câu hỏi</button>
                            </div>
                        ` : ''}
                        
                        ${evaluationData.has_quiz ? `
                            <div class="quiz-section evaluation-section">
                                <h3>📊 Quản lý bài trắc nghiệm</h3>
                                
                                <!-- Quiz Configuration Section -->
                                <div class="quiz-config-section">
                                    <h4>Cấu hình bài trắc nghiệm</h4>
                                    
                                    <div class="config-row">
                                        <label for="quizTimeLimit">⏱️ Thời gian làm bài (phút):</label>
                                        <input type="number" id="quizTimeLimit" class="config-input" 
                                               placeholder="Để trống nếu không giới hạn" 
                                               min="1" max="300"
                                               value="${quiz.quiz_time_limit || ''}">
                                        <span class="config-hint">Để trống nếu không muốn giới hạn thời gian</span>
                                    </div>
                                    
                                    <div class="config-row">
                                        <label for="quizPassingScore">✅ Điểm tối thiểu để đạt (%):</label>
                                        <input type="number" id="quizPassingScore" class="config-input" 
                                               placeholder="Ví dụ: 70" 
                                               min="0" max="100" step="0.01"
                                               value="${quiz.quiz_passing_score || ''}">
                                        <span class="config-hint">Điểm phần trăm tối thiểu để vượt qua bài kiểm tra (0-100)</span>
                                    </div>
                                    
                                    <div class="config-row">
                                        <label for="quizMaxAttempts">🔄 Số lần làm bài:</label>
                                        <select id="quizMaxAttempts" class="config-select">
                                            <option value="1" ${quiz.quiz_max_attempts === 1 ? 'selected' : ''}>1 lần</option>
                                            <option value="3" ${quiz.quiz_max_attempts === 3 ? 'selected' : ''}>3 lần</option>
                                            <option value="0" ${quiz.quiz_max_attempts === 0 || !quiz.quiz_max_attempts ? 'selected' : ''}>Không giới hạn</option>
                                        </select>
                                        <span class="config-hint">Số lần học viên được phép làm bài</span>
                                    </div>
                                    
                                    <button id="saveQuizConfig" class="save-config-btn">💾 Lưu cấu hình</button>
                                </div>
                                
                                <hr class="section-divider">
                                
                                <!-- Quiz File Upload Section -->
                                <div class="quiz-upload-area">
                                    <h4>Tải lên câu hỏi trắc nghiệm</h4>
                                    <input type="file" id="quizFileInput" accept=".xlsx,.xls" style="display: none;">
                                    <button id="uploadQuizBtn" class="upload-quiz-btn">Tải lên file Excel</button>
                                    <p class="upload-hint">Định dạng yêu cầu: Question, Choice_A, Choice_B, Choice_C, Choice_D, Correct_Answer</p>
                                </div>
                                
                                ${quiz.has_quiz_file ? `
                                    <div class="current-quiz-info">
                                        <p><strong>File hiện tại:</strong> ${quiz.quiz_file_name}</p>
                                        <button id="previewQuizBtn" class="preview-quiz-btn">Xem trước câu hỏi</button>
                                    </div>
                                ` : ''}
                                
                                <div id="quizPreview" class="quiz-preview" style="display: none;"></div>
                            </div>
                        ` : ''}
                        
                        ${!evaluationData.has_practical && !evaluationData.has_quiz ? `
                            <div class="no-evaluation">
                                <p>Không có hình thức kiểm tra cuối khóa nào được thiết lập cho khóa học này.</p>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="final-evaluation-modal-overlay"></div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listeners
        setupFinalEvaluationModalEvents(evaluationData, courseKey);

    }

    function setupFinalEvaluationModalEvents(evaluationData, courseKey) {
        const modal = document.getElementById('finalEvaluationModal');
        
        // Close modal
        modal.querySelector('.final-evaluation-close-btn').addEventListener('click', closeFinalEvaluationModal);
        modal.querySelector('.final-evaluation-modal-overlay').addEventListener('click', closeFinalEvaluationModal);
        
        // Practical evaluation events
        if (evaluationData.has_practical) {
            const savePracticalBtn = modal.querySelector('#savePracticalQuestion');
            if (savePracticalBtn) {
                savePracticalBtn.addEventListener('click', function() {
                    savePracticalQuestion(courseKey);
                });
            }
        }
        
        // Quiz evaluation events
        if (evaluationData.has_quiz) {
            // Save quiz configuration
            const saveConfigBtn = modal.querySelector('#saveQuizConfig');
            if (saveConfigBtn) {
                saveConfigBtn.addEventListener('click', function() {
                    saveQuizConfiguration(courseKey);
                });
            }
            
            const uploadBtn = modal.querySelector('#uploadQuizBtn');
            const fileInput = modal.querySelector('#quizFileInput');
            
            if (uploadBtn && fileInput) {
                uploadBtn.addEventListener('click', () => fileInput.click());
                fileInput.addEventListener('change', function(e) {
                    if (e.target.files.length > 0) {
                        uploadQuizFile(courseKey, e.target.files[0]);
                    }
                });
            }
            
            // Preview quiz
            const previewBtn = modal.querySelector('#previewQuizBtn');
            if (previewBtn) {
                previewBtn.addEventListener('click', function() {
                    previewQuiz(courseKey);
                });
            }
        }
    }

    function closeFinalEvaluationModal() {
        const modal = document.getElementById('finalEvaluationModal');
        if (modal) {
            modal.remove();
        }
    }

    function saveQuizConfiguration(courseKey) {
        const timeLimit = document.getElementById('quizTimeLimit').value;
        const passingScore = document.getElementById('quizPassingScore').value;
        const maxAttempts = document.getElementById('quizMaxAttempts').value;
        
        const configData = {
            quiz_time_limit: timeLimit ? parseInt(timeLimit) : null,
            quiz_passing_score: passingScore ? parseFloat(passingScore) : null,
            quiz_max_attempts: parseInt(maxAttempts)
        };
        
        fetch(`/api/chalix/evaluation/update/${courseKey}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(configData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('✅ Đã lưu cấu hình bài trắc nghiệm thành công!');
            } else {
                alert('❌ Lỗi: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error saving quiz configuration:', error);
            alert('❌ Lỗi khi lưu cấu hình');
        });
    }

    function savePracticalQuestion(courseKey) {
        const question = document.getElementById('practicalQuestion').value;
        
        fetch(`/api/chalix/evaluation/update/${courseKey}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                practical_question: question
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Đã lưu câu hỏi thành công!');
            } else {
                alert('Lỗi: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error saving question:', error);
            alert('Lỗi khi lưu câu hỏi');
        });
    }

    function uploadQuizFile(courseKey, file) {
        const formData = new FormData();
        formData.append('quiz_file', file);
        
        const uploadBtn = document.getElementById('uploadQuizBtn');
        const originalText = uploadBtn.textContent;
        uploadBtn.textContent = 'Đang tải lên...';
        uploadBtn.disabled = true;
        
        fetch(`/api/chalix/evaluation/upload-quiz/${courseKey}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Tải lên thành công! ${data.questions_count} câu hỏi đã được tạo.`);
                // Refresh modal to show new file info
                closeFinalEvaluationModal();
                openFinalEvaluationModal(courseKey);
            } else {
                alert('Lỗi: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error uploading quiz:', error);
            alert('Lỗi khi tải lên file');
        })
        .finally(() => {
            uploadBtn.textContent = originalText;
            uploadBtn.disabled = false;
        });
    }

    function previewQuiz(courseKey) {
        fetch(`/api/chalix/evaluation/preview-quiz/${courseKey}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showQuizPreview(data.questions);
                } else {
                    alert('Lỗi: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error previewing quiz:', error);
                alert('Lỗi khi xem trước câu hỏi');
            });
    }

    function showQuizPreview(questions) {
        const previewContainer = document.getElementById('quizPreview');
        
        let previewHTML = `<h4>Xem trước câu hỏi (${questions.length} câu)</h4>`;
        
        questions.forEach((question, index) => {
            previewHTML += `
                <div class="question-preview">
                    <h5>Câu ${index + 1}: ${question.question}</h5>
                    <ul class="choices-preview">
                        ${question.choices.map(choice => `
                            <li class="${choice.is_correct ? 'correct-choice' : ''}">${choice.text}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        });
        
        previewContainer.innerHTML = previewHTML;
        previewContainer.style.display = 'block';
    }

    function ensureFinalEvaluationModalStyles() {
        if (document.getElementById('finalEvaluationModalStyles')) return;
        
        const style = document.createElement('style');
        style.id = 'finalEvaluationModalStyles';
        style.textContent = `
            .final-evaluation-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .final-evaluation-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .final-evaluation-modal-content {
                position: relative;
                background: white;
                border-radius: 8px;
                width: 90%;
                max-width: 800px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
            
            .final-evaluation-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 24px;
                border-bottom: 1px solid #e0e0e0;
            }
            
            .final-evaluation-modal-header h2 {
                margin: 0;
                font-size: 20px;
                color: #333;
            }
            
            .final-evaluation-close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .final-evaluation-modal-body {
                padding: 24px;
            }
            
            .evaluation-info {
                background: #f5f5f5;
                padding: 16px;
                border-radius: 4px;
                margin-bottom: 20px;
            }
            
            .evaluation-types {
                display: flex;
                gap: 8px;
                margin-top: 8px;
            }
            
            .eval-type-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .eval-type-badge.practical {
                background: #e3f2fd;
                color: #1565c0;
            }
            
            .eval-type-badge.quiz {
                background: #f3e5f5;
                color: #7b1fa2;
            }
            
            .evaluation-section {
                margin-bottom: 30px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
            
            .evaluation-section h3 {
                margin: 0 0 16px 0;
                color: #333;
                font-size: 16px;
            }
            
            .no-evaluation {
                text-align: center;
                padding: 40px;
                color: #666;
                font-style: italic;
            }
            
            .practical-question-input {
                width: 100%;
                min-height: 120px;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                resize: vertical;
            }
            
            .save-practical-btn, .upload-quiz-btn, .preview-quiz-btn, .save-config-btn {
                background: #007cba;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 12px;
            }
            
            .save-practical-btn:hover, .upload-quiz-btn:hover, .preview-quiz-btn:hover, .save-config-btn:hover {
                background: #005a8b;
            }
            
            .quiz-config-section {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            
            .quiz-config-section h4 {
                margin: 0 0 16px 0;
                color: #333;
                font-size: 15px;
                font-weight: 600;
            }
            
            .config-row {
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .config-row label {
                font-weight: 500;
                color: #333;
                font-size: 14px;
            }
            
            .config-input, .config-select {
                padding: 10px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                max-width: 300px;
            }
            
            .config-input:focus, .config-select:focus {
                outline: none;
                border-color: #007cba;
                box-shadow: 0 0 0 3px rgba(0, 124, 186, 0.1);
            }
            
            .config-hint {
                font-size: 12px;
                color: #666;
                font-style: italic;
            }
            
            .section-divider {
                border: none;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }
            
            .save-config-btn {
                background: #28a745;
                font-weight: 500;
            }
            
            .save-config-btn:hover {
                background: #218838;
            }
            
            .upload-hint {
                font-size: 12px;
                color: #666;
                margin-top: 8px;
                margin-bottom: 0;
            }
            
            .current-quiz-info {
                background: #e8f4fd;
                padding: 12px;
                border-radius: 4px;
                margin: 16px 0;
            }
            
            .quiz-preview {
                margin-top: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 16px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .question-preview {
                margin-bottom: 16px;
                padding-bottom: 16px;
                border-bottom: 1px solid #eee;
            }
            
            .question-preview:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }
            
            .choices-preview {
                list-style: none;
                padding: 0;
                margin: 8px 0 0 0;
            }
            
            .choices-preview li {
                padding: 4px 0;
                margin-left: 20px;
            }
            
            .correct-choice {
                font-weight: bold;
                color: #2e7d32;
            }
        `;
        
        document.head.appendChild(style);
    }

    // Expose some functions globally for external use
    window.ChalixCMS = {
        activateTab: activateTab,
        loadTabData: loadTabData,
        openCreateProgramModalDirectly: openCreateProgramModalDirectly,
        openFinalEvaluationModal: openFinalEvaluationModal
    };
    // Notify other scripts that ChalixCMS is ready
    try {
        window.dispatchEvent(new Event('ChalixCMS:ready'));
    } catch (e) {
        console.warn('Could not dispatch ChalixCMS:ready event', e);
    }

    // Chalix CMS interface loaded (logs removed)

    }); // Close DOMContentLoaded listener

})();
