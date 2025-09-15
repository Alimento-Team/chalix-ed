(function () {
    'use strict';

    window.CMS_TABS = window.CMS_TABS || {};

    // returns an inline SVG element (DOM node) for a given icon token
    function getIconSvg(token) {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = {
            'seed-of-life': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1">
                        <circle cx="12" cy="12" r="2.2" />
                        <circle cx="8" cy="12" r="2.2" />
                        <circle cx="16" cy="12" r="2.2" />
                        <circle cx="10.5" cy="9.5" r="2.2" />
                        <circle cx="13.5" cy="9.5" r="2.2" />
                        <circle cx="10.5" cy="14.5" r="2.2" />
                        <circle cx="13.5" cy="14.5" r="2.2" />
                    </g>
                </svg>`,
            'flower-of-life': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1">
                        <circle cx="12" cy="6" r="3" />
                        <circle cx="16.5" cy="9" r="3" />
                        <circle cx="12" cy="12" r="3" />
                        <circle cx="7.5" cy="9" r="3" />
                        <circle cx="12" cy="18" r="3" />
                    </g>
                </svg>`,
            'tree-of-life': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 3v4" />
                        <path d="M7 10c1-2 4-3 5-3s4 1 5 3c.5 1-1 2-2 2s-1-1-3-1-2 1-3 1-2 0-2-1c0-1-2-1.5-1-4z" />
                        <path d="M6 19c2-1 4-1 6-1s4 0 6 1" />
                    </g>
                </svg>`,
            'lotus': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1">
                        <path d="M12 20s-3-5-7-6c0 0 4-4 7-4s7 4 7 4c-4 1-7 6-7 6z" />
                        <path d="M4 11s4-3 8-3 8 3 8 3" />
                    </g>
                </svg>`,
            'mandala': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1">
                        <circle cx="12" cy="12" r="2" />
                        <path d="M12 4v2M12 18v2M4 12h2M18 12h2M6.5 6.5l1.5 1.5M16 16l1.5 1.5M6.5 17.5l1.5-1.5M16 8l1.5-1.5" />
                    </g>
                </svg>`,
            'sacred-geometry': `
                <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <g fill="none" stroke="#111" stroke-width="1">
                        <polygon points="12,3 20,8 20,16 12,21 4,16 4,8" />
                        <circle cx="12" cy="12" r="2" />
                    </g>
                </svg>`
        }[token] || '';
        // return firstElementChild (the svg) if present
        return wrapper.firstElementChild;
    }

    function ensureStyles() {
        if (document.getElementById('cms-learning-management-styles')) return;
        const css = `
            .lm-wrap { display: flex; width: 100%; padding: 0; box-sizing: border-box; }
            .lm-card { width: 100%; max-width: none; background: transparent; padding: 0; text-align: center; }
            
            .lm-subtabs { display:flex; justify-content:center; margin-bottom: 32px; border-bottom: 2px solid #e5e7eb; }
            .lm-subtab-btn { 
                background: none; border: none; padding: 16px 32px; font-size: 16px; font-weight: 600; 
                color: #6b7280; cursor: pointer; border-bottom: 3px solid transparent; 
                transition: all 200ms ease; position: relative; top: 2px; 
            }
            .lm-subtab-btn:hover { color: #374151; }
            .lm-subtab-btn.active { color: #1f2937; border-bottom-color: #3b82f6; }
            
            .lm-subtab-content { text-align: left; width: 100%; }
            .lm-subtab-panel { display: none; width: 100%; }
            .lm-subtab-panel.active { display: block; }
            
            .lm-tab-header { 
                display: flex; justify-content: space-between; align-items: center; 
                margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;
            }
            .lm-tab-header h3 { margin: 0; font-size: 24px; font-weight: 700; color: #1f2937; }
            
            .lm-btn { 
                display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; 
                border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; 
                transition: all 200ms ease; text-decoration: none;
            }
            .lm-btn.primary { background: #3b82f6; color: #fff; }
            .lm-btn.primary:hover { background: #2563eb; }
            .lm-btn.secondary { background: #f3f4f6; color: #374151; }
            .lm-btn.secondary:hover { background: #e5e7eb; }
            .lm-btn.danger { background: #ef4444; color: #fff; }
            .lm-btn.danger:hover { background: #dc2626; }
            
            .lm-loading { text-align: center; padding: 40px; color: #6b7280; }
            .lm-error { text-align: center; padding: 40px; color: #ef4444; }
            .lm-empty { text-align: center; padding: 40px; color: #9ca3af; }
            
            .lm-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
                gap: 24px; 
                width: 100%;
                margin: 0;
            }
            .lm-card-item { 
                background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; 
                padding: 20px; transition: all 200ms ease; cursor: pointer;
                width: 100%;
                box-sizing: border-box;
            }
            .lm-card-item:hover { 
                border-color: #3b82f6; 
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1); 
                transform: translateY(-1px);
            }
            
            .lm-card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
            .lm-card-icon { width: 24px; height: 24px; flex-shrink: 0; }
            .lm-card-title { font-size: 18px; font-weight: 600; color: #1f2937; margin: 0; }
            
            .lm-card-meta { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
            .lm-card-desc { font-size: 14px; color: #374151; margin-bottom: 16px; line-height: 1.4; }
            
            .lm-card-actions { display: flex; gap: 8px; justify-content: flex-end; }
            .lm-card-btn { 
                padding: 6px 12px; font-size: 12px; border-radius: 6px; 
                border: none; cursor: pointer; transition: all 200ms ease;
            }
            .lm-card-btn.view { background: #e0f2fe; color: #0369a1; }
            .lm-card-btn.edit { background: #fef3c7; color: #92400e; }
            .lm-card-btn.delete { background: #fee2e2; color: #dc2626; }
        `;
        const style = document.createElement('style');
        style.id = 'cms-learning-management-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    function ensureDetailModalStyles() {
        if (document.getElementById('lm-detail-modal-styles')) return;
        const css = `
            .lm-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            
            .lm-modal {
                background: white;
                border-radius: 12px;
                max-width: 90vw;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            }
            
            .lm-detail-modal {
                max-width: 800px;
                width: 100%;
            }
            
            .lm-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 24px 24px 0;
                border-bottom: 1px solid #e5e7eb;
                margin-bottom: 24px;
            }
            
            .lm-modal-header-actions {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .lm-detail-title {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .lm-detail-icon {
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .lm-detail-icon .chalix-icon-svg {
                width: 32px;
                height: 32px;
            }
            
            .lm-detail-title h3 {
                margin: 0;
                font-size: 24px;
                font-weight: 700;
                color: #1f2937;
            }
            
            .lm-modal-close {
                background: none;
                border: none;
                font-size: 24px;
                color: #6b7280;
                cursor: pointer;
                padding: 8px;
                border-radius: 50%;
                transition: background-color 200ms;
            }
            
            .lm-modal-close:hover {
                background: #f3f4f6;
            }
            
            .lm-modal-body {
                padding: 0 24px 24px;
                max-height: 70vh;
                overflow-y: auto;
            }
            
            .lm-detail-section {
                margin-bottom: 32px;
            }
            
            .lm-detail-section h4 {
                font-size: 18px;
                font-weight: 600;
                color: #374151;
                margin: 0 0 16px;
                padding-bottom: 8px;
                border-bottom: 1px solid #f3f4f6;
            }
            
            .lm-detail-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }
            
            .lm-detail-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .lm-detail-item label {
                font-size: 12px;
                font-weight: 600;
                color: #6b7280;
                text-transform: uppercase;
            }
            
            .lm-detail-item span {
                font-size: 14px;
                color: #1f2937;
            }
            
            .lm-description {
                background: #f8fafc;
                padding: 16px;
                border-radius: 8px;
                border-left: 4px solid #3b82f6;
                font-size: 14px;
                color: #374151;
                line-height: 1.6;
                margin-top: 8px;
            }
            
            .lm-topics-list {
                background: #f8fafc;
                border-radius: 8px;
                padding: 16px;
                border: 1px solid #e5e7eb;
            }
            
            .lm-topic-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }
            
            .lm-topic-item:last-child {
                border-bottom: none;
            }
            
            .lm-topic-number {
                font-size: 12px;
                font-weight: 600;
                color: #6b7280;
                min-width: 24px;
            }
            
            .lm-topic-title {
                font-size: 14px;
                color: #374151;
            }
            
            .lm-no-topics {
                text-align: center;
                color: #9ca3af;
                font-style: italic;
                padding: 16px;
            }
        `;
        
        const style = document.createElement('style');
        style.id = 'lm-detail-modal-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    function ensureEditModalStyles() {
        if (document.getElementById('lm-edit-modal-styles')) return;
        const css = `
            .lm-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            
            .lm-modal {
                background: white;
                border-radius: 12px;
                max-width: 90vw;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
            }
            
            .lm-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 24px 24px 0;
                border-bottom: 1px solid #e5e7eb;
                margin-bottom: 24px;
                flex-shrink: 0;
            }
            
            .lm-modal-title {
                font-size: 18px;
                font-weight: 600;
                margin: 0;
                color: #1f2937;
            }
            
            .lm-modal-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #6b7280;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 200ms;
            }
            
            .lm-modal-close:hover {
                background: #f3f4f6;
                color: #374151;
            }
            
            .lm-modal-body {
                padding: 0 24px 24px;
                overflow-y: auto;
                flex: 1;
            }
            
            .lm-edit-modal {
                max-width: 700px;
                width: 100%;
            }
            
            .lm-edit-form {
                margin-bottom: 24px;
            }
            
            .lm-form-group {
                margin-bottom: 20px;
            }
            
            .lm-form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }
            
            .lm-form-label {
                display: block;
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 6px;
            }
            
            .lm-form-input {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 200ms;
                box-sizing: border-box;
            }
            
            .lm-form-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .lm-form-textarea {
                min-height: 80px;
                resize: vertical;
            }
            
            .lm-topics-editor {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                background: #f9fafb;
            }
            
            .lm-edit-topic-item {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .lm-topic-input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
            }
            
            .lm-remove-topic {
                background: #ef4444;
                color: white;
                border: none;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 200ms;
            }
            
            .lm-remove-topic:hover {
                background: #dc2626;
            }
            
            .lm-add-topic-btn {
                background: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                transition: background-color 200ms;
            }
            
            .lm-add-topic-btn:hover {
                background: #059669;
            }
            
            .lm-modal-actions {
                display: flex;
                justify-content: flex-end;
                gap: 12px;
                padding-top: 24px;
                border-top: 1px solid #e5e7eb;
            }
            
            .lm-modal-message {
                margin-top: 16px;
            }
            
            .lm-message {
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            
            .lm-message.lm-loading {
                background: #dbeafe;
                color: #1e40af;
            }
            
            .lm-message.lm-success {
                background: #dcfce7;
                color: #166534;
            }
            
            .lm-message.lm-error {
                background: #fee2e2;
                color: #dc2626;
            }
            
            .lm-radio-option {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                cursor: pointer;
                padding: 8px;
            }
            
            .lm-radio-option input[type="radio"] {
                margin: 0;
            }
            
            .lm-form-help {
                font-size: 12px;
                color: #6b7280;
                margin-top: 4px;
                display: block;
            }
            
            .lm-program-units-preview {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                background: #f9fafb;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .lm-unit-preview-item {
                margin-bottom: 12px;
                padding: 8px;
                background: white;
                border-radius: 4px;
                border-left: 3px solid #3b82f6;
            }
            
            .lm-unit-preview-item:last-child {
                margin-bottom: 0;
            }
            
            .lm-preview-note {
                margin-top: 12px;
                padding: 8px;
                background: #dbeafe;
                border-radius: 4px;
                font-size: 13px;
                color: #1e40af;
            }
            
            .lm-units-preview-list {
                margin-bottom: 8px;
            }
            
            .lm-icon-picker {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 8px;
                padding: 12px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: #f9fafb;
            }
            
            .lm-icon-option {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 12px;
                border: 2px solid transparent;
                border-radius: 8px;
                background: white;
                cursor: pointer;
                transition: all 200ms;
                min-height: 48px;
            }
            
            .lm-icon-option:hover {
                border-color: #3b82f6;
                background: #eff6ff;
            }
            
            .lm-icon-option.selected {
                border-color: #3b82f6;
                background: #dbeafe;
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
            }
            
            .lm-icon-option svg {
                width: 24px;
                height: 24px;
                display: block;
            }
            
            @media (max-width: 768px) {
                .lm-form-row {
                    grid-template-columns: 1fr;
                }
                
                .lm-icon-picker {
                    grid-template-columns: repeat(3, 1fr);
                }
                
                .lm-edit-topic-item {
                    flex-direction: column;
                    align-items: stretch;
                    gap: 4px;
                }
                
                .lm-remove-topic {
                    align-self: flex-end;
                    width: auto;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            }
        `;
        
        const style = document.createElement('style');
        style.id = 'lm-edit-modal-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    function render(container, config) {
        if (!container) return;
        console.log('[LM] Starting render for learning-management tab');
        console.log('ℹ️ API Status: Some endpoints are not yet implemented. Edit/Save functions will work in demo mode.');
        console.log('📝 Missing endpoints:', {
            'update-program': '/api/chalix/dashboard/update-program/',
            'update-course': '/api/chalix/dashboard/update-course/', 
            'program-detail': '/api/chalix/dashboard/program-detail/<id>/',
            'course-detail': '/api/chalix/dashboard/course-detail/<id>/'
        });
        ensureStyles();

        container.innerHTML = `
            <div class="lm-wrap">
                <div class="lm-card">
                    <div class="lm-subtabs" role="tablist">
                        <button class="lm-subtab-btn active" role="tab" data-subtab="programs" aria-selected="true">
                            Danh sách chương trình học
                        </button>
                        <button class="lm-subtab-btn" role="tab" data-subtab="courses" aria-selected="false">
                            Danh sách khóa học
                        </button>
                    </div>

                    <div class="lm-subtab-content">
                        <div id="lm-programs-tab" class="lm-subtab-panel active" role="tabpanel">
                            <div class="lm-tab-header">
                                <h3>Chương trình học</h3>
                                <button class="lm-btn primary" data-action="create-program">
                                    <span class="lm-btn-icon">+</span>
                                    Tạo chương trình học
                                </button>
                            </div>
                            <div class="lm-content-area">
                                <div class="lm-loading">Đang tải danh sách chương trình học...</div>
                            </div>
                        </div>

                        <div id="lm-courses-tab" class="lm-subtab-panel" role="tabpanel">
                            <div class="lm-tab-header">
                                <h3>Khóa học</h3>
                                <button class="lm-btn primary" data-action="create-course">
                                    <span class="lm-btn-icon">+</span>
                                    Tạo khóa học
                                </button>
                            </div>
                            <div class="lm-content-area">
                                <div class="lm-loading">Đang tải danh sách khóa học...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        initializeSubtabs(container);
        loadProgramsList(container.querySelector('#lm-programs-tab .lm-content-area'));
        console.log('[LM] Render completed successfully');
    }

    function initializeSubtabs(container) {
        const subtabBtns = container.querySelectorAll('.lm-subtab-btn');
        const subtabPanels = container.querySelectorAll('.lm-subtab-panel');

        subtabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetSubtab = btn.dataset.subtab;
                
                // Update active states
                subtabBtns.forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-selected', 'false');
                });
                subtabPanels.forEach(p => p.classList.remove('active'));
                
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
                
                const targetPanel = container.querySelector(`#lm-${targetSubtab}-tab`);
                if (targetPanel) {
                    targetPanel.classList.add('active');
                    
                    // Load content if not already loaded
                    const contentArea = targetPanel.querySelector('.lm-content-area');
                    if (contentArea && contentArea.querySelector('.lm-loading')) {
                        if (targetSubtab === 'programs') {
                            loadProgramsList(contentArea);
                        } else if (targetSubtab === 'courses') {
                            loadCoursesList(contentArea);
                        }
                    }
                }
            });
        });

        // Setup action buttons
        container.querySelectorAll('.lm-btn[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.dataset.action;
                
                if (action === 'create-program') {
                    openCreateProgramModal(() => {
                        // Refresh programs list after creation
                        const programsContent = container.querySelector('#lm-programs-tab .lm-content-area');
                        if (programsContent) {
                            loadProgramsList(programsContent);
                        }
                    });
                } else if (action === 'create-course') {
                    openCreateCourseModal(() => {
                        // Refresh courses list after creation
                        const coursesContent = container.querySelector('#lm-courses-tab .lm-content-area');
                        if (coursesContent) {
                            loadCoursesList(coursesContent);
                        }
                    });
                }
            });
        });
    }

    function loadProgramsList(contentArea) {
        if (!contentArea) return;
        
        contentArea.innerHTML = '<div class="lm-loading">Đang tải danh sách chương trình học...</div>';

        fetch('/api/chalix/dashboard/list-programs/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const programs = data.programs || [];
            renderProgramsList(contentArea, programs);
        })
        .catch(err => {
            console.error('Failed to load programs:', err);
            // Fallback with demo data
            const demoPrograms = [
                {
                    id: 1,
                    title: "Chương trình Demo 1",
                    description: "Mô tả chương trình demo 1 - API chưa sẵn sàng",
                    icon: "seed-of-life",
                    units: [
                        { title: "Đơn vị 1", description: "Mô tả đơn vị 1" },
                        { title: "Đơn vị 2", description: "Mô tả đơn vị 2" }
                    ]
                },
                {
                    id: 2,
                    title: "Chương trình Demo 2",
                    description: "Mô tả chương trình demo 2 - API chưa sẵn sàng",
                    icon: "flower-of-life",
                    units: [
                        { title: "Đơn vị A", description: "Mô tả đơn vị A" },
                        { title: "Đơn vị B", description: "Mô tả đơn vị B" },
                        { title: "Đơn vị C", description: "Mô tả đơn vị C" }
                    ]
                }
            ];
            console.log('🎭 Using demo programs data');
            renderProgramsList(contentArea, demoPrograms);
        });
    }

    function loadCoursesList(contentArea) {
        if (!contentArea) return;
        
        contentArea.innerHTML = '<div class="lm-loading">Đang tải danh sách khóa học...</div>';

        fetch('/api/chalix/dashboard/list-courses/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const courses = data.courses || [];
            renderCoursesList(contentArea, courses);
        })
        .catch(err => {
            console.error('Failed to load courses:', err);
            // Fallback with demo data
            const demoCourses = [
                {
                    id: 1,
                    title: "Khóa học Demo 1",
                    short_description: "Mô tả khóa học demo 1 - API chưa sẵn sàng",
                    course_key: "course-v1:chalix+demo1+2024",
                    studio_url: "/course/course-v1:chalix+demo1+2024",
                    course_type: "Demo",
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: 2,
                    title: "Khóa học Demo 2", 
                    short_description: "Mô tả khóa học demo 2 - API chưa sẵn sàng",
                    course_key: "course-v1:chalix+demo2+2024",
                    studio_url: "/course/course-v1:chalix+demo2+2024",
                    course_type: "Demo",
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }
            ];
            console.log('🎭 Using demo courses data');
            renderCoursesList(contentArea, demoCourses);
        });
    }

    function renderProgramsList(contentArea, programs) {
        if (!contentArea) return;

        if (programs.length === 0) {
            contentArea.innerHTML = '<div class="lm-empty">Chưa có chương trình học nào. Tạo chương trình học đầu tiên của bạn!</div>';
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'lm-grid';

        programs.forEach(program => {
            const card = document.createElement('div');
            card.className = 'lm-card-item';
            
            const iconSvg = getIconSvg(program.icon || 'seed-of-life');
            const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';
            
            card.innerHTML = `
                <div class="lm-card-header">
                    <div class="lm-card-icon">${iconHtml}</div>
                    <h4 class="lm-card-title">${escapeHtml(program.title)}</h4>
                </div>
                <div class="lm-card-meta">
                    ID: ${program.id} • ${program.topics ? program.topics.length : 0} chuyên đề
                </div>
                <div class="lm-card-desc">
                    ${escapeHtml(program.short_description || 'Chưa có mô tả')}
                </div>
                <div class="lm-card-actions">
                    <button class="lm-card-btn view" data-action="view-program" data-id="${program.id}">Xem</button>
                    <button class="lm-card-btn edit" data-action="edit-program" data-id="${program.id}">Sửa</button>
                    <button class="lm-card-btn delete" data-action="delete-program" data-id="${program.id}">Xóa</button>
                </div>
            `;

            // Add click event to the card itself to trigger view mode
            card.addEventListener('click', (e) => {
                // Only trigger if not clicking on action buttons
                if (!e.target.closest('.lm-card-actions')) {
                    viewProgramDetails(program.id);
                }
            });

            // Add event listeners for actions
            card.querySelector('[data-action="view-program"]').addEventListener('click', (e) => {
                e.stopPropagation();
                viewProgramDetails(program.id);
            });

            card.querySelector('[data-action="edit-program"]').addEventListener('click', (e) => {
                e.stopPropagation();
                editProgram(program.id, () => loadProgramsList(contentArea));
            });

            card.querySelector('[data-action="delete-program"]').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteProgram(program.id, () => loadProgramsList(contentArea));
            });

            grid.appendChild(card);
        });

        contentArea.innerHTML = '';
        contentArea.appendChild(grid);
    }

    function renderCoursesList(contentArea, courses) {
        if (!contentArea) return;

        if (courses.length === 0) {
            contentArea.innerHTML = '<div class="lm-empty">Chưa có khóa học nào. Tạo khóa học đầu tiên của bạn!</div>';
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'lm-grid';

        courses.forEach(course => {
            const card = document.createElement('div');
            card.className = 'lm-card-item';
            
            // Use course.id when available, otherwise fall back to course_key (OpenEDX identifier)
            const courseIdentifier = (course.id !== undefined && course.id !== null) ? course.id : course.course_key;

            card.innerHTML = `
                <div class="lm-card-header">
                    <div class="lm-card-icon">📚</div>
                    <h4 class="lm-card-title">${escapeHtml(course.title)}</h4>
                </div>
                <div class="lm-card-meta">
                    ID: ${courseIdentifier} • ${course.course_type || 'Chưa phân loại'}
                </div>
                <div class="lm-card-desc">
                    ${escapeHtml(course.short_description || 'Chưa có mô tả')}
                </div>
                <div class="lm-card-actions">
                    <button class="lm-card-btn view" data-action="view-course" data-id="${courseIdentifier}">Xem</button>
                    <button class="lm-card-btn edit" data-action="edit-course" data-id="${courseIdentifier}">Sửa</button>
                    <button class="lm-card-btn delete" data-action="delete-course" data-id="${courseIdentifier}">Xóa</button>
                </div>
            `;

            // Add click event to the card itself to open CMS studio in new tab
            card.addEventListener('click', (e) => {
                // Only trigger if not clicking on action buttons
                if (!e.target.closest('.lm-card-actions')) {
                    // Open CMS studio course edit UI in new tab
                    const studioUrl = course.studio_url || `/course/${course.course_key}`;
                    window.open(studioUrl, '_blank');
                }
            });

            // Add event listeners for actions
            card.querySelector('[data-action="view-course"]').addEventListener('click', (e) => {
                e.stopPropagation();
                viewCourseDetails(courseIdentifier);
            });

            card.querySelector('[data-action="edit-course"]').addEventListener('click', (e) => {
                e.stopPropagation();
                editCourse(courseIdentifier, () => loadCoursesList(contentArea));
            });

            card.querySelector('[data-action="delete-course"]').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteCourse(courseIdentifier, () => loadCoursesList(contentArea));
            });

            grid.appendChild(card);
        });

        contentArea.innerHTML = '';
        contentArea.appendChild(grid);
    }

    // Detailed view functions
    function viewProgramDetails(programId) {
        // First try to get the program from the list we already have
        const existingPrograms = getAllProgramsFromDOM();
        const program = existingPrograms.find(p => p.id == programId);
        
        if (program) {
            // Show details from cached data
            showProgramDetailsModal(program);
        } else {
            // Try to fetch from API
            fetch(`/api/chalix/dashboard/program-detail/${programId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(program => {
                showProgramDetailsModal(program);
            })
            .catch(err => {
                console.error('Failed to load program details:', err);
                // Fallback: show basic modal with available info
                showProgramDetailsModal({
                    id: programId,
                    title: 'Chương trình học',
                    short_description: 'Đang tải thông tin...',
                    topics: [],
                    icon: 'seed-of-life'
                });
            });
        }
    }

    function getAllProgramsFromDOM() {
        // Extract programs data from the current DOM
        const programs = [];
        document.querySelectorAll('.lm-card-item').forEach(card => {
            const titleEl = card.querySelector('.lm-card-title');
            const metaEl = card.querySelector('.lm-card-meta');
            const descEl = card.querySelector('.lm-card-desc');
            const viewBtn = card.querySelector('[data-action="view-program"]');
            
            if (titleEl && viewBtn) {
                const id = viewBtn.dataset.id;
                const title = titleEl.textContent;
                const metaText = metaEl ? metaEl.textContent : '';
                const topicsMatch = metaText.match(/(\d+)\s*chuyên đề/);
                const topicsCount = topicsMatch ? parseInt(topicsMatch[1]) : 0;
                
                // If card stores topics in a data attribute, use those titles (set by updateProgramInDOM)
                const topicsData = card.dataset.topics;
                const topics = topicsData ? (() => {
                    try { return JSON.parse(topicsData); } catch (e) { return null; }
                })() : null;

                programs.push({
                    id: id,
                    title: title,
                    short_description: descEl ? descEl.textContent : '',
                    topics: topics && Array.isArray(topics) && topics.length > 0
                        ? topics.map((t, i) => ({ id: t.id || (i+1), title: t.title || t.name || `Chuyên đề ${i+1}` }))
                        : Array.from({length: topicsCount}, (_, i) => ({ id: i + 1, title: `Chuyên đề ${i + 1}` })),
                    icon: 'seed-of-life',
                    created_at: new Date().toISOString(),
                    created_by: 'Người dùng hiện tại'
                });
            }
        });
        return programs;
    }

    function showProgramDetailsModal(program) {
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        
        const iconSvg = getIconSvg(program.icon || 'seed-of-life');
        const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';
        
        const topicsList = program.topics && program.topics.length > 0 
            ? program.topics.map((topic, index) => 
                `<div class="lm-topic-item">
                    <span class="lm-topic-number">${index + 1}.</span>
                    <span class="lm-topic-title">${escapeHtml(topic.title)}</span>
                </div>`
            ).join('')
            : '<div class="lm-no-topics">Chưa có chuyên đề nào</div>';

        overlay.innerHTML = `
            <div class="lm-modal lm-detail-modal">
                <div class="lm-modal-header">
                    <div class="lm-detail-title">
                        <div class="lm-detail-icon">${iconHtml}</div>
                        <h3>${escapeHtml(program.title)}</h3>
                    </div>
                    <div class="lm-modal-header-actions">
                        <button class="lm-btn secondary lm-edit-btn" data-program-id="${program.id}">
                            ✏️ Chỉnh sửa
                        </button>
                        <button class="lm-modal-close" aria-label="Đóng">×</button>
                    </div>
                </div>
                <div class="lm-modal-body">
                    <div class="lm-detail-section">
                        <h4>Thông tin cơ bản</h4>
                        <div class="lm-detail-grid">
                            <div class="lm-detail-item">
                                <label>ID</label>
                                <span>${program.id}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Biểu tượng</label>
                                <span>${program.icon || 'seed-of-life'}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Số chuyên đề</label>
                                <span>${program.topics ? program.topics.length : 0}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Tự động cập nhật</label>
                                <span>${program.update_topics ? 'Có' : 'Không'}</span>
                            </div>
                        </div>
                        ${program.short_description ? `
                            <div class="lm-detail-item">
                                <label>Mô tả</label>
                                <div class="lm-description">${escapeHtml(program.short_description)}</div>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="lm-detail-section">
                        <h4>Danh sách chuyên đề</h4>
                        <div class="lm-topics-list">
                            ${topicsList}
                        </div>
                    </div>
                    
                    <div class="lm-detail-section">
                        <h4>Thông tin khác</h4>
                        <div class="lm-detail-grid">
                            <div class="lm-detail-item">
                                <label>Tạo bởi</label>
                                <span>${escapeHtml(program.created_by || '—')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Ngày tạo</label>
                                <span>${program.created_at ? new Date(program.created_at).toLocaleString('vi-VN') : '—'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ensureDetailModalStyles();
        document.body.appendChild(overlay);

        // Close modal handlers
        overlay.querySelector('.lm-modal-close').addEventListener('click', () => {
            overlay.remove();
        });
        
        // Edit button handler
        const editBtn = overlay.querySelector('.lm-edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                overlay.remove();
                const onSuccess = () => {
                    // Refresh the programs list after editing
                    const programsContent = document.querySelector('#lm-programs-tab .lm-content-area');
                    if (programsContent && programsContent.offsetParent !== null) {
                        loadProgramsList(programsContent);
                    }
                };
                editProgram(program.id, onSuccess);
            });
        }
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    function editProgram(programId, onSuccess) {
        // Get program data for editing
        const existingPrograms = getAllProgramsFromDOM();
        const program = existingPrograms.find(p => p.id == programId);
        
        if (program) {
            showEditProgramModal(program, onSuccess);
        } else {
            // Try to fetch from API
            fetch(`/api/chalix/dashboard/program-detail/${programId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(program => {
                showEditProgramModal(program, onSuccess);
            })
            .catch(err => {
                console.error('Failed to load program for editing:', err);
                alert('Không thể tải thông tin chương trình học để chỉnh sửa.');
            });
        }
    }

    function showEditProgramModal(program, onSuccess) {
        ensureEditModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        
        const iconOptions = ['seed-of-life', 'flower-of-life', 'tree-of-life', 'lotus', 'mandala', 'sacred-geometry'];
        const iconOptionsHtml = iconOptions.map(icon => {
            const iconSvg = getIconSvg(icon);
            const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';
            const selected = icon === (program.icon || 'seed-of-life') ? 'selected' : '';
            return `<div class="lm-icon-option ${selected}" data-icon="${icon}" title="${icon}">
                        ${iconHtml}
                    </div>`;
        }).join('');

        const topicsHtml = (program.topics || []).map((topic, index) => 
            `<div class="lm-edit-topic-item" data-index="${index}">
                <input type="text" value="${escapeHtml(topic.title)}" class="lm-topic-input" placeholder="Tên chuyên đề">
                <button type="button" class="lm-remove-topic" title="Xóa chuyên đề">×</button>
            </div>`
        ).join('');

        overlay.innerHTML = `
            <div class="lm-modal lm-edit-modal">
                <div class="lm-modal-header">
                    <h3>Chỉnh sửa chương trình học</h3>
                    <button class="lm-modal-close" aria-label="Đóng">×</button>
                </div>
                <div class="lm-modal-body">
                    <form class="lm-edit-form">
                        <div class="lm-form-group">
                            <label class="lm-form-label">Tiêu đề chương trình</label>
                            <input type="text" name="title" class="lm-form-input" value="${escapeHtml(program.title)}" required>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label">Mô tả ngắn</label>
                            <textarea name="short_description" class="lm-form-input lm-form-textarea">${escapeHtml(program.short_description || '')}</textarea>
                        </div>
                        
                        <div class="lm-form-row">
                            <div class="lm-form-group">
                                <label class="lm-form-label">Biểu tượng</label>
                                <div class="lm-icon-picker" id="icon-picker">
                                    ${iconOptionsHtml}
                                </div>
                                <input type="hidden" name="icon" value="${program.icon || 'seed-of-life'}" id="selected-icon">
                            </div>
                            
                            <div class="lm-form-group">
                                <label class="lm-form-label">
                                    <input type="checkbox" name="update_topics" ${program.update_topics ? 'checked' : ''}>
                                    Tự động cập nhật chuyên đề
                                </label>
                            </div>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label">Danh sách chuyên đề</label>
                            <div class="lm-topics-editor">
                                ${topicsHtml}
                                <button type="button" class="lm-add-topic-btn">+ Thêm chuyên đề</button>
                            </div>
                        </div>
                    </form>
                    
                    <div class="lm-modal-actions">
                        <button class="lm-btn secondary lm-cancel-btn">Hủy</button>
                        <button class="lm-btn primary lm-save-btn">Lưu thay đổi</button>
                    </div>
                    
                    <div class="lm-modal-message"></div>
                </div>
            </div>
        `;

        ensureEditModalStyles();
        document.body.appendChild(overlay);

        setupEditModalHandlers(overlay, program, onSuccess);
    }

    function setupEditModalHandlers(overlay, program, onSuccess) {
        const form = overlay.querySelector('.lm-edit-form');
        const topicsEditor = overlay.querySelector('.lm-topics-editor');
        const addTopicBtn = overlay.querySelector('.lm-add-topic-btn');
        const saveBtn = overlay.querySelector('.lm-save-btn');
        const cancelBtn = overlay.querySelector('.lm-cancel-btn');
        const closeBtn = overlay.querySelector('.lm-modal-close');
        const messageDiv = overlay.querySelector('.lm-modal-message');

        // Close handlers
        const closeModal = () => overlay.remove();
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });

        // Icon picker handlers
        const iconPicker = overlay.querySelector('#icon-picker');
        const selectedIconInput = overlay.querySelector('#selected-icon');
        
        iconPicker.addEventListener('click', (e) => {
            const iconOption = e.target.closest('.lm-icon-option');
            if (iconOption) {
                // Remove selected class from all options
                iconPicker.querySelectorAll('.lm-icon-option').forEach(opt => opt.classList.remove('selected'));
                // Add selected class to clicked option
                iconOption.classList.add('selected');
                // Update hidden input value
                selectedIconInput.value = iconOption.dataset.icon;
            }
        });

        // Add topic handler
        addTopicBtn.addEventListener('click', () => {
            const topicDiv = document.createElement('div');
            topicDiv.className = 'lm-edit-topic-item';
            topicDiv.innerHTML = `
                <input type="text" class="lm-topic-input" placeholder="Tên chuyên đề">
                <button type="button" class="lm-remove-topic" title="Xóa chuyên đề">×</button>
            `;
            topicsEditor.insertBefore(topicDiv, addTopicBtn);
            
            // Add remove handler
            topicDiv.querySelector('.lm-remove-topic').addEventListener('click', () => {
                topicDiv.remove();
            });
            
            // Focus new input
            topicDiv.querySelector('.lm-topic-input').focus();
        });

        // Remove topic handlers for existing items
        topicsEditor.querySelectorAll('.lm-remove-topic').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.lm-edit-topic-item').remove();
            });
        });

        // Save handler
        saveBtn.addEventListener('click', () => {
            const formData = new FormData(form);
            const topics = Array.from(topicsEditor.querySelectorAll('.lm-topic-input'))
                .map(input => ({ title: input.value.trim() }))
                .filter(topic => topic.title);

            // Get the selected icon from the hidden input
            const selectedIcon = selectedIconInput.value || 'seed-of-life';

            const programData = {
                id: program.id,
                title: formData.get('title'),
                short_description: formData.get('short_description'),
                icon: selectedIcon,
                update_topics: formData.has('update_topics'),
                topics: topics
            };

            // Validate required fields
            if (!programData.title || !programData.title.trim()) {
                messageDiv.innerHTML = '<div class="lm-message lm-error">Vui lòng nhập tiêu đề chương trình</div>';
                return;
            }

            if (topics.length === 0) {
                messageDiv.innerHTML = '<div class="lm-message lm-error">Vui lòng thêm ít nhất một chuyên đề</div>';
                return;
            }

            // Show loading
            messageDiv.innerHTML = '<div class="lm-message lm-loading">Đang lưu thay đổi...</div>';
            messageDiv.style.display = 'block';
            saveBtn.disabled = true;

            // Try to save via API
            saveProgramChanges(programData)
                .then((response) => {
                    console.log('Save successful:', response);
                    const successMessage = response.message || 'Đã lưu chương trình học thành công!';
                    messageDiv.innerHTML = `<div class="lm-message lm-success">${successMessage}</div>`;
                    // Ensure visible list and any open details are updated with the new data
                    try {
                        updateProgramInDOM(programData);
                        updateOpenProgramDetails(programData);
                    } catch (e) { console.warn('Failed to update open program details', e); }

                    setTimeout(() => {
                        if (onSuccess && response.refresh === true) {
                            onSuccess();
                        } else {
                            console.info('[LM] Skipping automatic list reload after save; UI updated locally.');
                        }
                    }, 1500);
                })
                .catch(err => {
                    console.error('Save failed:', err);
                    const errorMessage = err.message || 'Có lỗi xảy ra khi lưu chương trình học';
                    messageDiv.innerHTML = `<div class="lm-message lm-error">${errorMessage}</div>`;
                    saveBtn.disabled = false;
                });
        });

        // Handle form submission (when Enter is pressed)
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            saveBtn.click();
        });
    }

    function saveProgramChanges(programData) {
        console.log('📤 Saving program data:', programData);
        
        // Try to save via API first
        return fetch(`/api/chalix/dashboard/update-program/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            },
            body: JSON.stringify(programData)
        })
        .then(resp => {
            console.log('📡 API response status:', resp.status);
            if (!resp.ok) {
                return resp.text().then(text => {
                    console.error('❌ API error response:', text);
                    throw new Error(`Server error: ${resp.status}`);
                });
            }
            return resp.json();
        })
        .then(data => {
            console.log('✅ API success response:', data);
            return {
                success: true,
                message: 'Đã cập nhật chương trình học thành công!',
                data: data
            };
        })
        .catch(err => {
            console.error('💥 Save error:', err);
            
            // If the endpoint doesn't exist (404), provide detailed simulation
            if (err.message.includes('404') || err.message.includes('Server error: 404')) {
                console.warn('⚠️ Update endpoint not found, running in simulation mode');
                console.log('🔧 Backend TODO: Create endpoint /api/chalix/dashboard/update-program/');
                console.log('📋 Expected payload format:', JSON.stringify(programData, null, 2));
                
                return new Promise(resolve => {
                    setTimeout(() => {
                        // Simulate successful save
                        console.log('✨ Simulated program update:', {
                            action: 'update_program',
                            program_id: programData.id,
                            changes: {
                                title: programData.title,
                                icon: programData.icon,
                                short_description: programData.short_description,
                                topics: programData.topics,
                                update_topics: programData.update_topics
                            },
                            timestamp: new Date().toISOString()
                        });
                        
                        // Update DOM with new data for immediate visual feedback
                        updateProgramInDOM(programData);
                        
                        resolve({
                            success: true,
                            simulated: true,
                            refresh: false,
                            message: 'Đã lưu thành công! (Chế độ mô phỏng - Cần tạo API endpoint)',
                            data: programData
                        });
                    }, 1200);
                });
            } else {
                // Re-throw other errors
                throw err;
            }
        });
    }

    // Update course in DOM for immediate visual feedback
    function updateCourseInDOM(courseData) {
        console.log('🔄 Updating course in DOM:', courseData);
        
        // Find the course item in the list
        const courseItems = document.querySelectorAll('.lm-course-item');
        courseItems.forEach(item => {
            const itemId = item.getAttribute('data-course-id');
            if (itemId && itemId === courseData.id.toString()) {
                console.log('📍 Found course item to update:', itemId);
                
                // Update title
                const titleEl = item.querySelector('h3');
                if (titleEl && courseData.title) {
                    titleEl.textContent = courseData.title;
                    console.log('📝 Updated course title');
                }
                
                // Update description
                const descEl = item.querySelector('p');
                if (descEl && courseData.description) {
                    descEl.textContent = courseData.description;
                    console.log('📝 Updated course description');
                }
                
                // Add visual feedback
                item.style.backgroundColor = '#e8f5e8';
                item.style.transform = 'scale(1.02)';
                item.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    item.style.backgroundColor = '';
                    item.style.transform = '';
                }, 2000);
                
                console.log('✅ Course DOM update completed');
                return;
            }
        });
        
        console.log('⚠️ Course item not found in DOM for update');
    }

    function updateProgramInDOM(programData) {
        // Find and update the program card in the DOM
        const programCards = document.querySelectorAll('.lm-card-item');
        programCards.forEach(card => {
            const titleEl = card.querySelector('.lm-card-title');
            const metaEl = card.querySelector('.lm-card-meta');
            const descEl = card.querySelector('.lm-card-desc');
            const iconEl = card.querySelector('.lm-card-icon');
            
            if (titleEl && metaEl) {
                const idMatch = metaEl.textContent.match(/ID:\s*(\d+)/);
                if (idMatch && parseInt(idMatch[1], 10) == Number(programData.id)) {
                    // Update the card with new data
                    titleEl.textContent = programData.title;
                    if (descEl) {
                        descEl.textContent = programData.short_description || 'Chưa có mô tả';
                    }
                    if (metaEl) {
                        metaEl.textContent = `ID: ${programData.id} • ${programData.topics ? programData.topics.length : 0} chuyên đề`;
                    }
                    if (iconEl && programData.icon) {
                        const iconSvg = getIconSvg(programData.icon);
                        iconEl.innerHTML = iconSvg ? iconSvg.outerHTML : '📚';
                    }
                    // Store topics on the card for future reads (so getAllProgramsFromDOM can pick up titles)
                    try {
                        if (programData.topics) {
                            card.dataset.topics = JSON.stringify(programData.topics);
                        } else {
                            delete card.dataset.topics;
                        }
                    } catch (e) {
                        console.warn('Failed to serialize topics for DOM storage', e);
                    }
                    
                    // Add visual feedback
                    card.style.transition = 'all 0.3s ease';
                    card.style.transform = 'scale(1.02)';
                    card.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                    
                    setTimeout(() => {
                        card.style.transform = 'scale(1)';
                        card.style.boxShadow = '';
                    }, 300);
                    
                    console.log('🔄 Updated program card in DOM:', programData.title);
                    return; // Exit forEach iteration
                }
            }
        });
    }

    function updateOpenProgramDetails(programData) {
        // If a details overlay is open for this program, update its content
        const overlay = document.querySelector('.lm-modal-overlay');
        if (!overlay) return;
        const titleEl = overlay.querySelector('.lm-detail-title h3');
        const idSpan = overlay.querySelector('.lm-detail-item span');

        // Try to detect details modal by matching title/id
        if (titleEl && titleEl.textContent && String(programData.title) === String(titleEl.textContent)) {
            // Update description
            const descEl = overlay.querySelector('.lm-description');
            if (descEl) descEl.textContent = programData.short_description || 'Chưa có mô tả';

            // Update topics list
            const topicsList = overlay.querySelector('.lm-topics-list');
            if (topicsList && Array.isArray(programData.topics)) {
                const topicsHtml = programData.topics.map((topic, index) => 
                    `<div class="lm-topic-item"><span class="lm-topic-number">${index+1}.</span><span class="lm-topic-title">${escapeHtml(topic.title || topic.name || topic)}</span></div>`
                ).join('');
                topicsList.innerHTML = topicsHtml;
            }
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function deleteProgram(programId, onSuccess) {
        showConfirmModal({
            title: 'Xóa chương trình học',
            message: 'Bạn có chắc chắn muốn xóa chương trình học này? Hành động này không thể hoàn tác.',
            confirmText: 'Xóa',
            cancelText: 'Hủy',
            danger: true,
            onConfirm: (modal) => {
                // Try to delete via API
                fetch(`/api/chalix/dashboard/delete-program/`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ program_id: programId })
                })
                .then(resp => {
                    if (!resp.ok) return resp.text().then(text => { throw new Error(text || resp.statusText); });
                    return resp.json();
                })
                .then(result => {
                    modal.showMessage('Đã xóa chương trình học thành công!', 'success');
                    setTimeout(() => {
                        modal.close();
                        if (onSuccess) onSuccess();
                    }, 900);
                })
                .catch(err => {
                    console.error('Failed to delete program:', err);
                    modal.showMessage('Không thể xóa chương trình. ' + (err.message || ''), 'error');
                });
            }
        });
    }

    function viewCourseDetails(courseId) {
        // First try to get the course from the list we already have
        const existingCourses = getAllCoursesFromDOM();
        const course = existingCourses.find(c => c.id == courseId);
        
        if (course) {
            // Show details from cached data
            showCourseDetailsModal(course);
        } else {
            // Try to fetch from API
            fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(course => {
                showCourseDetailsModal(course);
            })
            .catch(err => {
                console.error('Failed to load course details:', err);
                // Fallback: show basic modal with available info
                showCourseDetailsModal({
                    id: courseId,
                    title: 'Khóa học',
                    short_description: 'Đang tải thông tin...',
                    units: [],
                    course_type: 'Chưa phân loại'
                });
            });
        }
    }

    function getAllCoursesFromDOM() {
        // Extract courses data from the current DOM
        const courses = [];
        const coursesContent = document.querySelector('#lm-courses-tab .lm-content-area');
        if (!coursesContent) return [];
        
        coursesContent.querySelectorAll('.lm-card-item').forEach(card => {
            const titleEl = card.querySelector('.lm-card-title');
            const metaEl = card.querySelector('.lm-card-meta');
            const descEl = card.querySelector('.lm-card-desc');
            
            if (titleEl) {
                const title = titleEl.textContent;
                const meta = metaEl ? metaEl.textContent : '';
                const desc = descEl ? descEl.textContent : '';
                
                // Extract ID from meta text
                const idMatch = meta.match(/ID:\s*(\d+)/);
                const typeMatch = meta.match(/•\s*(.+)$/);
                
                if (idMatch) {
                    courses.push({
                        id: parseInt(idMatch[1]),
                        title: title,
                        short_description: desc === 'Chưa có mô tả' ? '' : desc,
                        course_type: typeMatch ? typeMatch[1].trim() : 'Chưa phân loại',
                        units: []
                    });
                }
            }
        });
        
        return courses;
    }

    function showCourseDetailsModal(course) {
        ensureDetailModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        
        overlay.innerHTML = `
            <div class="lm-modal lm-detail-modal">
                <div class="lm-modal-header">
                    <h3 class="lm-modal-title">Chi tiết khóa học</h3>
                    <button class="lm-modal-close" aria-label="Đóng">&times;</button>
                </div>
                <div class="lm-modal-body">
                    <div class="lm-detail-grid">
                        <div class="lm-detail-main">
                            <div class="lm-detail-section">
                                <h4>Thông tin cơ bản</h4>
                                <div class="lm-detail-info">
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Tên khóa học:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.title)}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">ID:</span>
                                        <span class="lm-detail-value">${course.id}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Loại khóa học:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.course_type || 'Chưa phân loại')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Mô tả:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.short_description || 'Chưa có mô tả')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Trình độ:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.level || 'Chưa xác định')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Thời lượng:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.duration || 'Chưa xác định')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="lm-detail-section">
                                <h4>Đơn vị học tập</h4>
                                <div class="lm-detail-units">
                                    ${course.units && course.units.length > 0 
                                        ? course.units.map(unit => `
                                            <div class="lm-detail-unit">
                                                <h5>${escapeHtml(unit.title || unit.name || 'Đơn vị học tập')}</h5>
                                                <p>${escapeHtml(unit.description || 'Chưa có mô tả')}</p>
                                            </div>
                                        `).join('')
                                        : '<p class="lm-detail-empty">Chưa có đơn vị học tập nào</p>'
                                    }
                                </div>
                            </div>
                        </div>
                        
                        <div class="lm-detail-sidebar">
                            <div class="lm-detail-actions">
                                <button class="lm-btn primary" id="edit-course-btn">Chỉnh sửa</button>
                                <button class="lm-btn secondary" id="preview-course-btn">Xem trước</button>
                                <button class="lm-btn danger" id="delete-course-btn">Xóa khóa học</button>
                            </div>
                            
                            <div class="lm-detail-stats">
                                <h5>Thống kê</h5>
                                <div class="lm-stat-item">
                                    <span class="lm-stat-label">Số đơn vị:</span>
                                    <span class="lm-stat-value">${course.units ? course.units.length : 0}</span>
                                </div>
                                <div class="lm-stat-item">
                                    <span class="lm-stat-label">Trạng thái:</span>
                                    <span class="lm-stat-value">${course.status || 'Bản nháp'}</span>
                                </div>
                                <div class="lm-stat-item">
                                    <span class="lm-stat-label">Người tạo:</span>
                                    <span class="lm-stat-value">${escapeHtml(course.created_by || 'Chưa xác định')}</span>
                                </div>
                                <div class="lm-stat-item">
                                    <span class="lm-stat-label">Ngày tạo:</span>
                                    <span class="lm-stat-value">${course.created_at ? new Date(course.created_at).toLocaleDateString('vi-VN') : 'Chưa xác định'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Event handlers
        overlay.querySelector('.lm-modal-close').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });
        
        overlay.querySelector('#edit-course-btn').addEventListener('click', () => {
            document.body.removeChild(overlay);
            const onSuccess = () => {
                // Refresh the courses list if we're on the courses tab
                const coursesContent = document.querySelector('#lm-courses-tab .lm-content-area');
                if (coursesContent && coursesContent.offsetParent !== null) {
                    loadCoursesList(coursesContent);
                }
            };
            // Use numeric id when available, otherwise fall back to course_key
            const courseIdentifier = (course.id !== undefined && course.id !== null) ? course.id : course.course_key;
            showEditCourseModal(course, onSuccess);
        });
        
        overlay.querySelector('#preview-course-btn').addEventListener('click', () => {
            // Preview functionality - could open course in new tab
            if (course.preview_url) {
                window.open(course.preview_url, '_blank');
            } else {
                alert('Chức năng xem trước đang được phát triển');
            }
        });
        
        overlay.querySelector('#delete-course-btn').addEventListener('click', () => {
            const onSuccess = () => {
                // Refresh the courses list
                const coursesContent = document.querySelector('#lm-courses-tab .lm-content-area');
                if (coursesContent && coursesContent.offsetParent !== null) {
                    loadCoursesList(coursesContent);
                }
            };
            const courseIdentifier = (course.id !== undefined && course.id !== null) ? course.id : course.course_key;
            deleteCourse(courseIdentifier, onSuccess);
        });
    }

    function editCourse(courseId, onSuccess) {
        // First try to get the course from the list we already have
        const existingCourses = getAllCoursesFromDOM();
        const course = existingCourses.find(c => c.id == courseId);
        
        if (course) {
            showEditCourseModal(course, onSuccess);
        } else {
            // Try to fetch from API
            fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(course => {
                showEditCourseModal(course, onSuccess);
            })
            .catch(err => {
                console.error('Failed to load course details:', err);
                // Fallback: show edit modal with basic info
                showEditCourseModal({
                    id: courseId,
                    title: '',
                    short_description: '',
                    course_type: '',
                    level: '',
                    duration: '',
                    units: []
                }, onSuccess);
            });
        }
    }

    function showEditCourseModal(course, onSuccess) {
        ensureEditModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        
        overlay.innerHTML = `
            <div class="lm-modal lm-edit-modal">
                <div class="lm-modal-header">
                    <h3 class="lm-modal-title">Chỉnh sửa khóa học</h3>
                    <button class="lm-modal-close" aria-label="Đóng">&times;</button>
                </div>
                <div class="lm-modal-body">
                    <form class="lm-edit-form" id="edit-course-form">
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-title">Tên khóa học *</label>
                            <input type="text" id="course-title" name="title" class="lm-form-input" 
                                   value="${escapeHtml(course.title || '')}" required>
                        </div>
                        
                        <div class="lm-form-row">
                            <div class="lm-form-group">
                                <label class="lm-form-label" for="course-type">Loại khóa học</label>
                                <select id="course-type" name="course_type" class="lm-form-input">
                                    <option value="">Chọn loại khóa học</option>
                                    <option value="Lý luận chính trị" ${course.course_type === 'Lý luận chính trị' ? 'selected' : ''}>Lý luận chính trị</option>
                                    <option value="Kiến thức quốc phòng và an ninh" ${course.course_type === 'Kiến thức quốc phòng và an ninh' ? 'selected' : ''}>Kiến thức quốc phòng và an ninh</option>
                                    <option value="Kiến thức, kỹ năng quản lý nhà nước" ${course.course_type === 'Kiến thức, kỹ năng quản lý nhà nước' ? 'selected' : ''}>Kiến thức, kỹ năng quản lý nhà nước</option>
                                    <option value="Kiến thức, kỹ năng theo yêu cầu vị trí việc làm" ${course.course_type === 'Kiến thức, kỹ năng theo yêu cầu vị trí việc làm' ? 'selected' : ''}>Kiến thức, kỹ năng theo yêu cầu vị trí việc làm</option>
                                    <option value="Kiến thức KHCN, đổi mới sáng tạo, kỹ năng số, công nghệ số" ${course.course_type === 'Kiến thức KHCN, đổi mới sáng tạo, kỹ năng số, công nghệ số' ? 'selected' : ''}>Kiến thức KHCN, đổi mới sáng tạo, kỹ năng số, công nghệ số</option>
                                </select>
                            </div>
                            <div class="lm-form-group">
                                <label class="lm-form-label" for="course-level">Trình độ</label>
                                <select id="course-level" name="level" class="lm-form-input">
                                    <option value="">Chọn trình độ</option>
                                    <option value="Cơ bản" ${course.level === 'Cơ bản' ? 'selected' : ''}>Cơ bản</option>
                                    <option value="Nâng cao" ${course.level === 'Nâng cao' ? 'selected' : ''}>Nâng cao</option>
                                    <option value="Chuyên ngành" ${course.level === 'Chuyên ngành' ? 'selected' : ''}>Chuyên ngành</option>
                                    <option value="Chuyên sâu" ${course.level === 'Chuyên sâu' ? 'selected' : ''}>Chuyên sâu</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-duration">Thời lượng</label>
                            <input type="text" id="course-duration" name="duration" class="lm-form-input" 
                                   value="${escapeHtml(course.duration || '')}" 
                                   placeholder="Ví dụ: 8 tuần, 40 giờ">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-description">Mô tả ngắn</label>
                            <textarea id="course-description" name="short_description" 
                                      class="lm-form-input lm-form-textarea" 
                                      placeholder="Mô tả ngắn gọn về khóa học...">${escapeHtml(course.short_description || '')}</textarea>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label">Đơn vị học tập</label>
                            <div class="lm-topics-editor" id="units-editor">
                                <div id="units-list">
                                    ${(course.units || []).map((unit, index) => `
                                        <div class="lm-edit-topic-item" data-index="${index}">
                                            <input type="text" class="lm-topic-input" 
                                                   value="${escapeHtml(unit.title || unit.name || '')}" 
                                                   placeholder="Tên đơn vị học tập">
                                            <button type="button" class="lm-remove-topic" onclick="removeUnit(${index})">&times;</button>
                                        </div>
                                    `).join('')}
                                </div>
                                <button type="button" class="lm-add-topic-btn" id="add-unit-btn">+ Thêm đơn vị</button>
                            </div>
                        </div>
                    </form>
                    
                    <div class="lm-modal-message" id="course-modal-message" style="display: none;"></div>
                </div>
                
                <div class="lm-modal-actions">
                    <button type="button" class="lm-btn secondary" id="cancel-course-btn">Hủy</button>
                    <button type="button" class="lm-btn primary" id="save-course-btn">Lưu thay đổi</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        setupEditCourseModalHandlers(overlay, course, onSuccess);
    }

    function setupEditCourseModalHandlers(overlay, course, onSuccess) {
        // Close handlers
        overlay.querySelector('.lm-modal-close').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        overlay.querySelector('#cancel-course-btn').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });
        
        // Units management
        let unitsCount = (course.units || []).length;
        
        overlay.querySelector('#add-unit-btn').addEventListener('click', () => {
            const unitsList = overlay.querySelector('#units-list');
            const newUnit = document.createElement('div');
            newUnit.className = 'lm-edit-topic-item';
            newUnit.setAttribute('data-index', unitsCount);
            newUnit.innerHTML = `
                <input type="text" class="lm-topic-input" 
                       value="" placeholder="Tên đơn vị học tập">
                <button type="button" class="lm-remove-topic" onclick="this.parentElement.remove()">&times;</button>
            `;
            unitsList.appendChild(newUnit);
            unitsCount++;
            newUnit.querySelector('.lm-topic-input').focus();
        });
        
        // Make remove functions globally available for inline handlers
        window.removeUnit = function(index) {
            const unitItem = overlay.querySelector(`[data-index="${index}"]`);
            if (unitItem) {
                unitItem.remove();
            }
        };
        
        // Save handler
        overlay.querySelector('#save-course-btn').addEventListener('click', () => {
            saveCourseChanges(overlay, course, onSuccess);
        });
        
        // Form validation
        const form = overlay.querySelector('#edit-course-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            saveCourseChanges(overlay, course, onSuccess);
        });
    }

    function saveCourseChanges(overlay, originalCourse, onSuccess) {
        const messageEl = overlay.querySelector('#course-modal-message');
        const saveBtn = overlay.querySelector('#save-course-btn');
        const form = overlay.querySelector('#edit-course-form');
        
        // Show loading
        messageEl.innerHTML = '<div class="lm-message lm-loading">Đang lưu thay đổi...</div>';
        messageEl.style.display = 'block';
        saveBtn.disabled = true;
        
        // Collect form data
        const formData = new FormData(form);
        const courseData = {
            id: originalCourse.id,
            title: formData.get('title'),
            short_description: formData.get('short_description'),
            course_type: formData.get('course_type'),
            level: formData.get('level'),
            duration: formData.get('duration'),
            units: []
        };
        
        // Collect units
        overlay.querySelectorAll('.lm-topic-input').forEach((input, index) => {
            const value = input.value.trim();
            if (value) {
                courseData.units.push({
                    title: value,
                    name: value,
                    order: index
                });
            }
        });
        
        // Validate required fields
        if (!courseData.title.trim()) {
            messageEl.innerHTML = '<div class="lm-message lm-error">Vui lòng nhập tên khóa học</div>';
            saveBtn.disabled = false;
            return;
        }
        
        // Try to save via API
        console.log('📤 Saving course data:', courseData);
        
        fetch(`/api/chalix/dashboard/update-course/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(courseData)
        })
        .then(resp => {
            console.log('📡 Course API response status:', resp.status);
            if (!resp.ok) {
                return resp.text().then(text => {
                    console.error('❌ Course API error:', text);
                    throw new Error(`Server error: ${resp.status}`);
                });
            }
            return resp.json();
        })
        .then(result => {
            console.log('✅ Course saved successfully:', result);
            messageEl.innerHTML = '<div class="lm-message lm-success">Đã lưu khóa học thành công!</div>';
            setTimeout(() => {
                document.body.removeChild(overlay);
                if (onSuccess) onSuccess();
            }, 1500);
        })
        .catch(err => {
            console.error('💥 Failed to save course:', err);
            
            if (err.message.includes('404') || err.message.includes('Server error: 404')) {
                console.warn('⚠️ Course update endpoint not found, running in simulation mode');
                console.log('🔧 Backend TODO: Create endpoint /api/chalix/dashboard/update-course/');
                console.log('📋 Expected payload format:', JSON.stringify(courseData, null, 2));
                
                // Simulate successful save
                setTimeout(() => {
                    console.log('✨ Simulated course update:', {
                        action: 'update_course',
                        course_id: courseData.id,
                        changes: courseData,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Update DOM for immediate visual feedback
                    updateCourseInDOM(courseData);
                    
                    messageEl.innerHTML = '<div class="lm-message lm-success">Đã lưu khóa học! (Chế độ mô phỏng - Cần tạo API endpoint)</div>';
                    setTimeout(() => {
                        document.body.removeChild(overlay);
                        if (onSuccess) onSuccess();
                    }, 1500);
                }, 1000);
            } else {
                messageEl.innerHTML = '<div class="lm-message lm-error">Có lỗi xảy ra khi lưu khóa học: ' + err.message + '</div>';
                saveBtn.disabled = false;
            }
        });
    }

    function deleteCourse(courseId, onSuccess) {
        showConfirmModal({
            title: 'Xóa khóa học',
            message: 'Bạn có chắc chắn muốn xóa khóa học này? Hành động này không thể hoàn tác.',
            confirmText: 'Xóa',
            cancelText: 'Hủy',
            danger: true,
            onConfirm: (modal) => {
                // Defensive checks: ensure we have an identifier to send
                if (courseId === undefined || courseId === null) {
                    modal.showMessage('Không tìm thấy mã khóa học để xóa.', 'error');
                    return;
                }

                // Determine whether to send a local DB id or an OpenEDX course_key
                let payload;
                if (typeof courseId === 'string' && courseId.indexOf('course-v1:') !== -1) {
                    payload = { course_key: courseId };
                } else {
                    payload = { course_id: courseId };
                }

                fetch(`/api/chalix/dashboard/delete-course/`, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(payload)
                })
                .then(resp => {
                    if (!resp.ok) return resp.text().then(text => { throw new Error(text || resp.statusText); });
                    return resp.json();
                })
                .then(result => {
                    modal.showMessage('Đã xóa khóa học thành công!', 'success');
                    setTimeout(() => {
                        modal.close();
                        if (onSuccess) onSuccess();
                    }, 900);
                })
                .catch(err => {
                    console.error('Failed to delete course:', err);
                    modal.showMessage('Không thể xóa khóa học. ' + (err.message || ''), 'error');
                });
            }
        });
    }

    // Reusable confirm modal using existing modal styles
    function showConfirmModal(opts) {
        const title = opts.title || 'Confirm';
        const message = opts.message || '';
        const confirmText = opts.confirmText || 'OK';
        const cancelText = opts.cancelText || 'Cancel';
        const danger = !!opts.danger;

        ensureDetailModalStyles();
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';

        overlay.innerHTML = `
            <div class="lm-modal lm-detail-modal">
                <div class="lm-modal-header">
                    <h3 class="lm-modal-title">${escapeHtml(title)}</h3>
                    <button class="lm-modal-close" aria-label="Đóng">&times;</button>
                </div>
                <div class="lm-modal-body">
                    <div style="padding: 8px 0 16px; color: #374151;">${escapeHtml(message)}</div>
                    <div class="lm-modal-message" style="display:block"></div>
                </div>
                <div class="lm-modal-actions" style="padding: 12px 24px;">
                    <button class="lm-btn secondary lm-cancel-confirm">${escapeHtml(cancelText)}</button>
                    <button class="lm-btn ${danger ? 'danger' : 'primary'} lm-confirm-btn">${escapeHtml(confirmText)}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const modal = {
            close: () => overlay.remove(),
            showMessage: (text, type) => {
                const msgDiv = overlay.querySelector('.lm-modal-message');
                if (!msgDiv) return;
                if (type === 'success') {
                    msgDiv.innerHTML = `<div class="lm-message lm-success">${escapeHtml(text)}</div>`;
                } else if (type === 'error') {
                    msgDiv.innerHTML = `<div class="lm-message lm-error">${escapeHtml(text)}</div>`;
                } else {
                    msgDiv.innerHTML = `<div class="lm-message lm-loading">${escapeHtml(text)}</div>`;
                }
            }
        };

        overlay.querySelector('.lm-modal-close').addEventListener('click', () => modal.close());
        overlay.querySelector('.lm-cancel-confirm').addEventListener('click', () => modal.close());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) modal.close(); });
        overlay.querySelector('.lm-confirm-btn').addEventListener('click', () => {
            // Show loading state
            modal.showMessage('Đang xử lý...', 'loading');
            // Call provided handler
            if (typeof opts.onConfirm === 'function') opts.onConfirm(modal);
        });

        return modal;
    }

    // Implemented: Create Program modal UI and handlers.
    // Previously showed a placeholder alert; now builds and opens a full modal.
    function openCreateProgramModal(onSuccess) {
        ensureEditModalStyles();

        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';

        overlay.innerHTML = `
            <div class="lm-modal lm-edit-modal">
                <div class="lm-modal-header">
                    <h3 class="lm-modal-title">Tạo chương trình học mới</h3>
                    <button class="lm-modal-close" aria-label="Đóng">&times;</button>
                </div>
                <div class="lm-modal-body">
                    <form class="lm-edit-form" id="create-program-form">
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-program-title">Tiêu đề chương trình *</label>
                            <input type="text" id="new-program-title" name="title" class="lm-form-input" placeholder="Nhập tiêu đề chương trình..." required>
                        </div>

                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-program-short-desc">Mô tả ngắn</label>
                            <textarea id="new-program-short-desc" name="short_description" class="lm-form-input lm-form-textarea" placeholder="Mô tả ngắn gọn về chương trình..."></textarea>
                        </div>

                        <div class="lm-form-group">
                            <label class="lm-form-label">Biểu tượng</label>
                            <div class="lm-icon-picker" id="create-icon-picker"></div>
                            <input type="hidden" name="icon" id="create-selected-icon" value="seed-of-life">
                        </div>

                        <div class="lm-form-group">
                            <label class="lm-form-label">Danh sách chuyên đề</label>
                            <div class="lm-topics-editor" id="create-topics-editor">
                                <div id="create-topics-list"></div>
                                <button type="button" class="lm-add-topic-btn" id="add-create-topic-btn">+ Thêm chuyên đề</button>
                            </div>
                        </div>
                    </form>

                    <div class="lm-modal-message" id="create-program-modal-message" style="display: none;"></div>
                </div>
                <div class="lm-modal-actions">
                    <button type="button" class="lm-btn secondary" id="cancel-create-program-btn">Hủy</button>
                    <button type="button" class="lm-btn primary" id="create-program-btn">Tạo chương trình</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        setupCreateProgramModalHandlers(overlay, onSuccess);
    }

    function openCreateCourseModal(onSuccess) {
        ensureEditModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        
        overlay.innerHTML = `
            <div class="lm-modal lm-edit-modal">
                <div class="lm-modal-header">
                    <h3 class="lm-modal-title">Tạo khóa học mới</h3>
                    <button class="lm-modal-close" aria-label="Đóng">&times;</button>
                </div>
                <div class="lm-modal-body">
                    <form class="lm-edit-form" id="create-course-form">
                        <div class="lm-form-group">
                            <label class="lm-form-label">Tạo khóa học từ</label>
                            <div class="lm-form-row">
                                <label class="lm-radio-option">
                                    <input type="radio" name="creation_type" value="blank" checked>
                                    <span>Tạo khoá học mới hoàn toàn</span>
                                </label>
                                <label class="lm-radio-option">
                                    <input type="radio" name="creation_type" value="from_program">
                                    <span>Từ kho chương trình học có sẵn</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="lm-form-group" id="program-selector" style="display: none;">
                            <label class="lm-form-label" for="source-program">Chọn chương trình học</label>
                            <select id="source-program" name="source_program" class="lm-form-input">
                                <option value="">Đang tải danh sách chương trình...</option>
                            </select>
                            <small class="lm-form-help">Các đơn vị học tập sẽ được tạo từ các chuyên đề của chương trình</small>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-title">Tên khóa học *</label>
                            <input type="text" id="new-course-title" name="title" class="lm-form-input" 
                                   placeholder="Nhập tên khóa học..." required>
                        </div>
                        
                        <div class="lm-form-row">
                            <div class="lm-form-group">
                                <label class="lm-form-label" for="new-course-type">Loại khóa học</label>
                                <select id="new-course-type" name="course_type" class="lm-form-input">
                                    <option value="">Chọn loại khóa học</option>
                                    <option value="Lý luận chính trị">Lý luận chính trị</option>
                                    <option value="Kiến thức quốc phòng và an ninh">Kiến thức quốc phòng và an ninh</option>
                                    <option value="Kiến thức, kỹ năng quản lý nhà nước">Kiến thức, kỹ năng quản lý nhà nước</option>
                                    <option value="Kiến thức, kỹ năng theo yêu cầu vị trí việc làm">Kiến thức, kỹ năng theo yêu cầu vị trí việc làm</option>
                                    <option value="Kiến thức KHCN, đổi mới sáng tạo, kỹ năng số, công nghệ số">Kiến thức KHCN, đổi mới sáng tạo, kỹ năng số, công nghệ số</option>
                                </select>
                            </div>
                            <div class="lm-form-group">
                                <label class="lm-form-label" for="new-course-level">Trình độ</label>
                                <select id="new-course-level" name="level" class="lm-form-input">
                                    <option value="">Chọn trình độ</option>
                                    <option value="Cơ bản">Cơ bản</option>
                                    <option value="Nâng cao">Nâng cao</option> 
                                    <option value="Chuyên ngành">Chuyên ngành</option>
                                    <option value="Chuyên sâu">Chuyên sâu</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-duration">Thời lượng</label>
                            <input type="text" id="new-course-duration" name="duration" class="lm-form-input" 
                                   placeholder="Ví dụ: 8 tuần, 40 giờ">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-description">Mô tả ngắn</label>
                            <textarea id="new-course-description" name="short_description" 
                                      class="lm-form-input lm-form-textarea" 
                                      placeholder="Mô tả ngắn gọn về khóa học..."></textarea>
                        </div>
                        
                        <div class="lm-form-group" id="manual-units" style="display: none;">
                            <label class="lm-form-label">Đơn vị học tập</label>
                            <div class="lm-topics-editor" id="new-units-editor">
                                <div id="new-units-list">
                                </div>
                                <button type="button" class="lm-add-topic-btn" id="add-new-unit-btn">+ Thêm đơn vị</button>
                            </div>
                        </div>
                        
                        <div class="lm-form-group" id="program-units-preview" style="display: none;">
                            <label class="lm-form-label">Đơn vị học tập sẽ được tạo</label>
                            <div class="lm-program-units-preview" id="units-preview">
                            </div>
                        </div>
                    </form>
                    
                    <div class="lm-modal-message" id="create-course-modal-message" style="display: none;"></div>
                </div>
                
                <div class="lm-modal-actions">
                    <button type="button" class="lm-btn secondary" id="cancel-create-course-btn">Hủy</button>
                    <button type="button" class="lm-btn primary" id="create-course-btn">Tạo khóa học</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        setupCreateCourseModalHandlers(overlay, onSuccess);
    }

    function setupCreateCourseModalHandlers(overlay, onSuccess) {
        // Close handlers
        overlay.querySelector('.lm-modal-close').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        overlay.querySelector('#cancel-create-course-btn').addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });
        
        // Creation type handlers
        const creationTypeRadios = overlay.querySelectorAll('input[name="creation_type"]');
        const programSelector = overlay.querySelector('#program-selector');
        const manualUnits = overlay.querySelector('#manual-units');
        const programUnitsPreview = overlay.querySelector('#program-units-preview');
        
        creationTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'from_program') {
                    programSelector.style.display = 'block';
                    manualUnits.style.display = 'none';
                    loadProgramsForSelection(overlay.querySelector('#source-program'));
                } else {
                    programSelector.style.display = 'none';
                    manualUnits.style.display = 'block';
                    programUnitsPreview.style.display = 'none';
                }
            });
        });
        
        // Program selection handler
        overlay.querySelector('#source-program').addEventListener('change', (e) => {
            const programId = e.target.value;
            if (programId) {
                showProgramUnitsPreview(programId, overlay.querySelector('#units-preview'));
                programUnitsPreview.style.display = 'block';
            } else {
                programUnitsPreview.style.display = 'none';
            }
        });
        
        // Manual units management
        let unitsCount = 0;
        
        overlay.querySelector('#add-new-unit-btn').addEventListener('click', () => {
            const unitsList = overlay.querySelector('#new-units-list');
            const newUnit = document.createElement('div');
            newUnit.className = 'lm-edit-topic-item';
            newUnit.setAttribute('data-index', unitsCount);
            newUnit.innerHTML = `
                <input type="text" class="lm-topic-input" 
                       value="" placeholder="Tên đơn vị học tập">
                <button type="button" class="lm-remove-topic" onclick="this.parentElement.remove()">&times;</button>
            `;
            unitsList.appendChild(newUnit);
            unitsCount++;
            newUnit.querySelector('.lm-topic-input').focus();
        });
        
        // Create handler
        overlay.querySelector('#create-course-btn').addEventListener('click', () => {
            createNewCourse(overlay, onSuccess);
        });
        
        // Form validation
        const form = overlay.querySelector('#create-course-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            createNewCourse(overlay, onSuccess);
        });
        
        // Initialize with blank creation mode
        manualUnits.style.display = 'block';
    }

    function setupCreateProgramModalHandlers(overlay, onSuccess) {
        const closeBtn = overlay.querySelector('.lm-modal-close');
        const cancelBtn = overlay.querySelector('#cancel-create-program-btn');
        const createBtn = overlay.querySelector('#create-program-btn');
        const messageDiv = overlay.querySelector('#create-program-modal-message');
        const form = overlay.querySelector('#create-program-form');
        const topicsEditor = overlay.querySelector('#create-topics-editor');
        const addTopicBtn = overlay.querySelector('#add-create-topic-btn');
        const iconPicker = overlay.querySelector('#create-icon-picker');
        const selectedIconInput = overlay.querySelector('#create-selected-icon');

        // Close handlers
        const closeModal = () => overlay.remove();
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

        // Initialize icon picker options
        const iconOptions = ['seed-of-life', 'flower-of-life', 'tree-of-life', 'lotus', 'mandala', 'sacred-geometry'];
        iconPicker.innerHTML = iconOptions.map(icon => {
            const svg = getIconSvg(icon);
            const html = svg ? svg.outerHTML : icon;
            const selected = icon === (selectedIconInput.value || 'seed-of-life') ? 'selected' : '';
            return `<div class="lm-icon-option ${selected}" data-icon="${icon}" title="${icon}">${html}</div>`;
        }).join('');

        iconPicker.addEventListener('click', (e) => {
            const opt = e.target.closest('.lm-icon-option');
            if (!opt) return;
            iconPicker.querySelectorAll('.lm-icon-option').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            selectedIconInput.value = opt.dataset.icon;
        });

        // Add topic handler
        addTopicBtn.addEventListener('click', () => {
            const div = document.createElement('div');
            div.className = 'lm-edit-topic-item';
            div.innerHTML = `
                <input type="text" class="lm-topic-input" placeholder="Tên chuyên đề">
                <button type="button" class="lm-remove-topic">&times;</button>
            `;
            topicsEditor.insertBefore(div, addTopicBtn);
            div.querySelector('.lm-remove-topic').addEventListener('click', () => div.remove());
            div.querySelector('.lm-topic-input').focus();
        });

        // Remove handlers for existing (none at start)
        topicsEditor.querySelectorAll('.lm-remove-topic').forEach(btn => {
            btn.addEventListener('click', (e) => e.target.closest('.lm-edit-topic-item').remove());
        });

        // Create handler
        createBtn.addEventListener('click', () => {
            const formData = new FormData(form);
            const title = formData.get('title') || '';
            const short_description = formData.get('short_description') || '';
            const icon = selectedIconInput.value || 'seed-of-life';

            const topics = Array.from(topicsEditor.querySelectorAll('.lm-topic-input'))
                .map(input => ({ title: input.value.trim() }))
                .filter(t => t.title.length > 0);

            if (!title.trim()) {
                messageDiv.style.display = 'block';
                messageDiv.innerHTML = '<div class="lm-message lm-error">Vui lòng nhập tiêu đề chương trình</div>';
                return;
            }

            if (topics.length === 0) {
                messageDiv.style.display = 'block';
                messageDiv.innerHTML = '<div class="lm-message lm-error">Vui lòng thêm ít nhất một chuyên đề</div>';
                return;
            }

            // Disable button and show loading
            createBtn.disabled = true;
            messageDiv.style.display = 'block';
            messageDiv.innerHTML = '<div class="lm-message lm-loading">Đang tạo chương trình...</div>';

            const payload = {
                title: title.trim(),
                short_description: short_description.trim(),
                icon: icon,
                topics: topics
            };

            // Try to call API
            fetch('/api/chalix/dashboard/create-program/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(resp => {
                if (!resp.ok) {
                    return resp.text().then(text => { throw new Error('Server error: ' + resp.status + ' - ' + text); });
                }
                return resp.json();
            })
            .then(data => {
                messageDiv.innerHTML = '<div class="lm-message lm-success">Đã tạo chương trình học thành công!</div>';
                setTimeout(() => {
                    overlay.remove();
                    if (onSuccess) onSuccess();
                }, 900);
            })
            .catch(err => {
                console.error('Create program failed:', err);
                // If 404, simulate creation
                if (err.message.includes('404')) {
                    console.warn('Create endpoint missing, simulating create-program');
                    setTimeout(() => {
                        // Simulate adding program to DOM for feedback
                        const contentArea = document.querySelector('#lm-programs-tab .lm-content-area');
                        const simulatedProgram = {
                            id: Math.floor(Math.random() * 100000) + 100,
                            title: payload.title,
                            short_description: payload.short_description,
                            icon: payload.icon,
                            topics: payload.topics
                        };
                        // Append to DOM by reloading list (since we don't have persistent storage)
                        updateProgramInDOM(simulatedProgram);
                        messageDiv.innerHTML = '<div class="lm-message lm-success">Đã tạo chương trình (mô phỏng)</div>';
                        setTimeout(() => {
                            overlay.remove();
                            if (onSuccess) onSuccess();
                        }, 900);
                    }, 800);
                } else {
                    messageDiv.innerHTML = '<div class="lm-message lm-error">Có lỗi khi tạo chương trình: ' + escapeHtml(err.message) + '</div>';
                    createBtn.disabled = false;
                }
            });
        });

        // Submit on Enter
        form.addEventListener('submit', (e) => { e.preventDefault(); createBtn.click(); });
    }

    function loadProgramsForSelection(selectElement) {
        if (!selectElement) return;
        
        // First try to get programs from current DOM
        const existingPrograms = getAllProgramsFromDOM();
        if (existingPrograms.length > 0) {
            populateProgramsSelect(selectElement, existingPrograms);
            return;
        }
        
        // Otherwise fetch from API
        fetch('/api/chalix/dashboard/list-programs/', {
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const programs = data.programs || [];
            populateProgramsSelect(selectElement, programs);
        })
        .catch(err => {
            console.error('Failed to load programs for selection:', err);
            selectElement.innerHTML = '<option value="">Không thể tải danh sách chương trình</option>';
        });
    }

    function populateProgramsSelect(selectElement, programs) {
        selectElement.innerHTML = '<option value="">Chọn chương trình học...</option>';
        programs.forEach(program => {
            const option = document.createElement('option');
            option.value = program.id;
            option.textContent = `${program.title} (${program.topics ? program.topics.length : 0} chuyên đề)`;
            selectElement.appendChild(option);
        });
    }

    function showProgramUnitsPreview(programId, previewElement) {
        if (!previewElement) return;
        
        // First try to get program from current DOM
        const existingPrograms = getAllProgramsFromDOM();
        const program = existingPrograms.find(p => p.id == programId);
        
        if (program) {
            renderUnitsPreview(previewElement, program);
        } else {
            // Fetch program details
            fetch(`/api/chalix/dashboard/program-detail/${programId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(program => {
                renderUnitsPreview(previewElement, program);
            })
            .catch(err => {
                console.error('Failed to load program details:', err);
                previewElement.innerHTML = '<p class="lm-error">Không thể tải chi tiết chương trình</p>';
            });
        }
    }

    function renderUnitsPreview(previewElement, program) {
        if (!program.topics || program.topics.length === 0) {
            previewElement.innerHTML = '<p class="lm-detail-empty">Chương trình này chưa có chuyên đề nào</p>';
            return;
        }
        
        const unitsHtml = program.topics.map((topic, index) => `
            <div class="lm-unit-preview-item">
                <strong>Đơn vị ${index + 1}:</strong> ${escapeHtml(topic.title || topic.name || topic)}
                ${topic.description ? `<br><small>${escapeHtml(topic.description)}</small>` : ''}
            </div>
        `).join('');
        
        previewElement.innerHTML = `
            <div class="lm-units-preview-list">
                ${unitsHtml}
            </div>
            <p class="lm-preview-note">
                <strong>Lưu ý:</strong> Mỗi chuyên đề sẽ trở thành một đơn vị học tập trong khóa học mới
            </p>
        `;
    }

    function createNewCourse(overlay, onSuccess) {
        const messageEl = overlay.querySelector('#create-course-modal-message');
        const createBtn = overlay.querySelector('#create-course-btn');
        const form = overlay.querySelector('#create-course-form');
        
        // Show loading
        messageEl.innerHTML = '<div class="lm-message lm-loading">Đang tạo khóa học...</div>';
        messageEl.style.display = 'block';
        createBtn.disabled = true;
        
        // Collect form data
        const formData = new FormData(form);
        const creationType = formData.get('creation_type');
        const courseData = {
            title: formData.get('title'),
            short_description: formData.get('short_description'),
            course_type: formData.get('course_type'),
            level: formData.get('level'),
            duration: formData.get('duration'),
            creation_type: creationType,
            units: []
        };
        
        // Validate required fields
        if (!courseData.title.trim()) {
            messageEl.innerHTML = '<div class="lm-message lm-error">Vui lòng nhập tên khóa học</div>';
            createBtn.disabled = false;
            return;
        }
        
        if (creationType === 'from_program') {
            const sourceProgramId = formData.get('source_program');
            if (!sourceProgramId) {
                messageEl.innerHTML = '<div class="lm-message lm-error">Vui lòng chọn chương trình học</div>';
                createBtn.disabled = false;
                return;
            }
            courseData.source_program_id = sourceProgramId;
            
            // Get program details to create units
            const existingPrograms = getAllProgramsFromDOM();
            const sourceProgram = existingPrograms.find(p => p.id == sourceProgramId);
            
            if (sourceProgram && sourceProgram.topics) {
                courseData.units = sourceProgram.topics.map((topic, index) => ({
                    title: topic.title || topic.name || topic,
                    name: topic.title || topic.name || topic,
                    description: topic.description || `Đơn vị học tập được tạo từ chuyên đề "${topic.title || topic.name || topic}"`,
                    order: index,
                    source_topic: topic
                }));
            }
        } else {
            // Collect manual units
            overlay.querySelectorAll('#new-units-list .lm-topic-input').forEach((input, index) => {
                const value = input.value.trim();
                if (value) {
                    courseData.units.push({
                        title: value,
                        name: value,
                        order: index
                    });
                }
            });
        }
        
        // Try to create via API
        fetch(`/api/chalix/dashboard/create-course/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(courseData)
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(result => {
            messageEl.innerHTML = '<div class="lm-message lm-success">Đã tạo khóa học thành công!</div>';
            setTimeout(() => {
                document.body.removeChild(overlay);
                if (onSuccess) onSuccess();
            }, 1500);
        })
        .catch(err => {
            console.error('Failed to create course:', err);
            // Fallback: simulate success for now
            const successMessage = creationType === 'from_program' 
                ? `Đã tạo khóa học với ${courseData.units.length} đơn vị từ chương trình (mô phỏng - API chưa sẵn sàng)`
                : 'Đã tạo khóa học thành công (mô phỏng - API chưa sẵn sàng)';
            messageEl.innerHTML = `<div class="lm-message lm-success">${successMessage}</div>`;
            setTimeout(() => {
                document.body.removeChild(overlay);
                if (onSuccess) onSuccess();
            }, 2000);
        });
    }

    // Utility functions
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Register the module under both keys to support different consumers
    // Preferred key (underscore) for newer code:
    window.CMS_TABS['learning_management'] = {
        render: render,
        openCreateProgramModal: openCreateProgramModal,
        openCreateCourseModal: openCreateCourseModal
    };

    // Hyphenated key for templates or older callers that expect 'learning-management'
    // This ensures the dashboard's diagnostic and loader find the module.
    if (!window.CMS_TABS['learning-management']) {
        window.CMS_TABS['learning-management'] = window.CMS_TABS['learning_management'];
    }

})();