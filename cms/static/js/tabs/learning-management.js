(function () {
    'use strict';
    
    console.log('Learning Management JS loaded - with DEBUGGING evaluation modes v1.4');

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
                grid-template-columns: 1fr 320px;
                gap: 24px;
                margin-bottom: 16px;
            }

            @media (max-width: 900px) {
                .lm-detail-grid {
                    grid-template-columns: 1fr;
                }
                .lm-detail-sidebar {
                    order: 2;
                }
                .lm-detail-main {
                    order: 1;
                }
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

            .lm-detail-main {
                min-width: 0;
            }

            .lm-detail-sidebar {
                padding: 8px 12px;
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
                    ID: ${program.id} • ${program.topics_count || (program.topics ? program.topics.length : 0)} chuyên đề
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
            // Store course_key on the DOM node so getAllCoursesFromDOM can recover it later
            if (course.course_key) {
                card.dataset.courseKey = course.course_key;
            }
            // Store new fields for later detail view / edit operations
            if (course.course_type) {
                card.dataset.courseType = course.course_type;
            }
            if (course.course_level) {
                card.dataset.courseLevel = course.course_level;
            }
            if (course.online_course_link) {
                card.dataset.onlineCourseLink = course.online_course_link;
            }
            if (course.instructor) {
                card.dataset.instructor = course.instructor;
            }
            if (course.estimated_hours !== undefined && course.estimated_hours !== null) {
                card.dataset.estimatedHours = course.estimated_hours;
            }
            
            // Use course.id when available, otherwise fall back to course_key (OpenEDX identifier)
            const courseIdentifier = (course.id !== undefined && course.id !== null) ? course.id : course.course_key;

            card.innerHTML = `
                <div class="lm-card-header">
                    <div class="lm-card-icon">📚</div>
                    <h4 class="lm-card-title">${escapeHtml(course.title)}</h4>
                </div>
                <div class="lm-card-meta">
                    ID: ${courseIdentifier} • ${course.course_type || 'Chưa phân loại'} • ${
                        course.course_level === 'basic' ? 'Cơ bản' :
                        course.course_level === 'intermediate' ? 'Trung cấp' :
                        course.course_level === 'advanced' ? 'Nâng cao' :
                        course.course_level || 'Chưa xác định trình độ'
                    }
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
        // Always fetch fresh data from API to ensure topics are current
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
            // Fallback: try to get basic data from DOM but without fake topics
            const existingPrograms = getAllProgramsFromDOM();
            const program = existingPrograms.find(p => p.id == programId);
            if (program) {
                // Remove fake topics and show modal with loading message
                program.topics = [];
                showProgramDetailsModal(program);
            } else {
                // Fallback: show basic modal with available info
                showProgramDetailsModal({
                    id: programId,
                    title: 'Chương trình học',
                    short_description: 'Đang tải thông tin...',
                    topics: [],
                    icon: 'seed-of-life'
                });
            }
        });
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
                        ? topics
                        : [], // Don't generate fake topics - let API provide real data
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
        
        const topicsList = generateTopicsListHtml(program.topics);

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
                            <div class="lm-detail-item">
                                <label>Hình thức kiểm tra cuối khoá</label>
                                <span>${program.allow_practical_submission ? 'Nộp bài thực hành' : 'Làm bài trắc nghiệm'}</span>
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
        // Always fetch fresh data from API to ensure topics are current
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
                        
                        <!-- Evaluation mode switch (Nộp bài thu hoạch / Làm bài trắc nghiệm) -->
                        <div class="lm-form-group">
                            <label class="lm-form-label">Hình thức kiểm tra cuối khoá</label>
                            <div style="display:flex;align-items:center;gap:12px;">
                                <div id="practical-option" style="padding:8px 12px;border-radius:8px;background:${program.allow_practical_submission ? '#e3f2fd' : 'transparent'};cursor:pointer;">Nộp bài thu hoạch</div>
                                <label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;">
                                    <input type="checkbox" id="evaluation-mode-switch" name="evaluation_mode" ${program.allow_practical_submission ? '' : 'checked'} style="opacity:0;width:0;height:0;">
                                    <div id="evaluation-switch-ui" style="width:46px;height:26px;border-radius:20px;background:${program.allow_practical_submission ? '#d1d5db' : '#3b82f6'};position:relative;transition:background 200ms;">
                                        <div id="evaluation-switch-knob" style="width:20px;height:20px;background:#fff;border-radius:50%;position:absolute;top:3px;left:${program.allow_practical_submission ? '3px' : '23px'};transition:left 200ms;"></div>
                                    </div>
                                </label>
                                <div id="quiz-option" style="padding:8px 12px;border-radius:8px;background:${program.allow_practical_submission ? 'transparent' : '#e3f2fd'};cursor:pointer;">Làm bài trắc nghiệm</div>
                            </div>
                            <div class="lm-form-help">Chọn hình thức kiểm tra cuối khoá cho chương trình này</div>
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

        // Evaluation switch handlers
        const evalCheckbox = overlay.querySelector('#evaluation-mode-switch');
        const evalUi = overlay.querySelector('#evaluation-switch-ui');
        const evalKnob = overlay.querySelector('#evaluation-switch-knob');
        const practicalOption = overlay.querySelector('#practical-option');
        const quizOption = overlay.querySelector('#quiz-option');

        // Evaluation switch setup - ON=Quiz, OFF=Practical
        function setEvaluationMode(isPractical) {
            // Always query fresh from overlay to ensure elements exist
            const checkbox = overlay.querySelector('#evaluation-mode-switch');
            const ui = overlay.querySelector('#evaluation-switch-ui');
            const knob = overlay.querySelector('#evaluation-switch-knob');
            const practical = overlay.querySelector('#practical-option');
            const quiz = overlay.querySelector('#quiz-option');
            
            console.log('setEvaluationMode called with:', isPractical, 'Elements found:', {
                checkbox: !!checkbox,
                ui: !!ui,
                knob: !!knob,
                practical: !!practical,
                quiz: !!quiz
            });
            
            // REVERSED LOGIC: checkbox ON = quiz, OFF = practical
            const isQuizMode = !isPractical;
            
            // Update checkbox state (ON for quiz, OFF for practical)
            if (checkbox) {
                checkbox.checked = isQuizMode;
            }
            
            // Update switch UI appearance (blue when ON/quiz, gray when OFF/practical)
            if (ui) {
                ui.style.background = isQuizMode ? '#3b82f6' : '#d1d5db';
            }
            
            // Update knob position (right when ON/quiz, left when OFF/practical)
            if (knob) {
                knob.style.left = isQuizMode ? '23px' : '3px';
            }
            
            // Update option backgrounds
            if (practical) {
                practical.style.background = isPractical ? '#e3f2fd' : 'transparent';
            }
            
            if (quiz) {
                quiz.style.background = isQuizMode ? '#e3f2fd' : 'transparent';
            }
            
            console.log('Evaluation mode set to:', isPractical ? 'Practical (Nộp bài thu hoạch) - Switch OFF' : 'Quiz (Làm bài trắc nghiệm) - Switch ON');
        }

        // Initialize with program data
        const initialPractical = !!program.allow_practical_submission;
        setEvaluationMode(initialPractical);
        console.log('Initialized evaluation switch. Program allows practical:', program.allow_practical_submission, 
                   'Switch will be:', initialPractical ? 'OFF (Practical)' : 'ON (Quiz)');

        // Click handlers with event delegation and fresh DOM queries
        overlay.addEventListener('click', (e) => {
            const target = e.target;
            
            // Handle switch UI clicks - toggle between modes
            if (target.id === 'evaluation-switch-ui' || target.id === 'evaluation-switch-knob') {
                e.preventDefault();
                const checkbox = overlay.querySelector('#evaluation-mode-switch');
                if (checkbox) {
                    // Since checkbox ON = quiz, OFF = practical
                    // If checkbox is currently ON (quiz), toggle to OFF (practical)
                    // If checkbox is currently OFF (practical), toggle to ON (quiz)
                    const currentlyQuiz = checkbox.checked;
                    const newIsPractical = currentlyQuiz; // Toggle to opposite
                    setEvaluationMode(newIsPractical);
                    console.log('Switch UI clicked, toggled to:', newIsPractical ? 'Practical' : 'Quiz');
                }
            }
            
            // Handle practical option clicks - always set to practical
            else if (target.id === 'practical-option' || target.closest('#practical-option')) {
                e.preventDefault();
                setEvaluationMode(true); // Set to practical (switch OFF)
                console.log('Practical option selected');
            }
            
            // Handle quiz option clicks - always set to quiz
            else if (target.id === 'quiz-option' || target.closest('#quiz-option')) {
                e.preventDefault();
                setEvaluationMode(false); // Set to quiz (switch ON)
                console.log('Quiz option selected');
            }
        });

        // Save handler
        saveBtn.addEventListener('click', () => {
            const formData = new FormData(form);
            const topics = Array.from(topicsEditor.querySelectorAll('.lm-topic-input'))
                .map(input => ({ title: input.value.trim() }))
                .filter(topic => topic.title);

            // Get the selected icon from the hidden input
            const selectedIcon = selectedIconInput.value || 'seed-of-life';

            const evalCheckboxValue = overlay.querySelector('#evaluation-mode-switch').checked;
            const programData = {
                id: program.id,
                title: formData.get('title'),
                short_description: formData.get('short_description'),
                icon: selectedIcon,
                update_topics: formData.has('update_topics'),
                // REVERSED LOGIC: checkbox ON = quiz (allow_multiple_choice), OFF = practical (allow_practical_submission)
                allow_practical_submission: evalCheckboxValue === false,
                allow_multiple_choice: evalCheckboxValue === true,
                topics: topics
            };

            console.log('Saving program data:', {
                evalCheckboxValue,
                allow_practical_submission: programData.allow_practical_submission,
                allow_multiple_choice: programData.allow_multiple_choice,
                fullProgramData: programData
            });

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
                    console.log('Updated program data being used to update UI:', programData);
                    const successMessage = response.message || 'Đã lưu chương trình học thành công!';
                    messageDiv.innerHTML = `<div class="lm-message lm-success">${successMessage}</div>`;
                    // Ensure visible list and any open details are updated with the new data
                    try {
                        updateProgramInDOM(programData);
                        updateOpenProgramDetails(programData);
                        console.log('UI update calls completed');
                    } catch (e) { 
                        console.warn('Failed to update UI after save:', e); 
                    }

                    setTimeout(() => {
                        // Always refresh after save to ensure fresh data
                        overlay.remove();
                        console.log('Closing edit modal and refreshing program list');
                        if (onSuccess) {
                            onSuccess();
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
        
        // Find the course item in the list - support both legacy '.lm-course-item' and new '.lm-card-item'
        const courseItems = document.querySelectorAll('.lm-course-item, .lm-card-item');
        let found = false;
        courseItems.forEach(item => {
            // Prefer dataset.courseKey when available
            const cardCourseKey = item.dataset.courseKey;
            const metaEl = item.querySelector && item.querySelector('.lm-card-meta');
            let metaId = null;
            if (metaEl) {
                const m = metaEl.textContent.match(/ID:\s*([^•\n]+)/);
                metaId = m ? m[1].trim() : null;
            }

            const itemId = item.getAttribute('data-course-id') || metaId || null;

            // Match by numeric id or by course_key string
            if ((courseData.id && String(courseData.id) === String(itemId)) ||
                (courseData.course_key && cardCourseKey && String(courseData.course_key) === String(cardCourseKey))) {
                found = true;

                // Update title if present
                const titleEl = item.querySelector('h3, .lm-card-title');
                if (titleEl && courseData.title) {
                    titleEl.textContent = courseData.title;
                }

                // Update short description if present
                const descEl = item.querySelector('p, .lm-card-desc');
                if (descEl && (courseData.short_description || courseData.description)) {
                    descEl.textContent = courseData.short_description || courseData.description || '';
                }

                // Update stored dataset fields so future DOM reads include them
                try {
                    if (courseData.course_key) item.dataset.courseKey = courseData.course_key;
                    if (courseData.course_type !== undefined) item.dataset.courseType = courseData.course_type || '';
                    if (courseData.course_level !== undefined) item.dataset.courseLevel = courseData.course_level || '';
                    if (courseData.online_course_link !== undefined) item.dataset.onlineCourseLink = courseData.online_course_link || '';
                    if (courseData.instructor !== undefined) item.dataset.instructor = courseData.instructor || '';
                    // Always set estimatedHours to avoid leaving stale values on the card.
                    // Store as a string; clear to empty string when no value provided.
                    if (courseData.estimated_hours !== undefined && courseData.estimated_hours !== null) {
                        item.dataset.estimatedHours = String(courseData.estimated_hours);
                    } else {
                        item.dataset.estimatedHours = '';
                    }
                } catch (e) {
                    console.warn('Failed to update card dataset', e);
                }

                // Visual feedback
                item.style.transition = 'all 0.25s ease';
                item.style.transform = 'scale(1.02)';
                item.style.boxShadow = '0 6px 18px rgba(0,0,0,0.08)';
                setTimeout(() => {
                    item.style.transform = '';
                    item.style.boxShadow = '';
                }, 300);

                console.log('✅ Updated course card in DOM');
                return;
            }
        });

        if (!found) console.log('⚠️ Course item not found in DOM for update');
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
                        const topicsCount = programData.topics_count || (programData.topics ? programData.topics.length : 0);
                        metaEl.textContent = `ID: ${programData.id} • ${topicsCount} chuyên đề`;
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

            // Update evaluation setting display
            const detailItems = overlay.querySelectorAll('.lm-detail-item');
            detailItems.forEach(item => {
                const label = item.querySelector('label');
                if (label && label.textContent === 'Hình thức kiểm tra cuối khoá') {
                    const valueSpan = item.querySelector('span');
                    if (valueSpan) {
                        valueSpan.textContent = programData.allow_practical_submission ? 'Nộp bài thực hành' : 'Làm bài trắc nghiệm';
                    }
                }
            });

            // Update topics list
            const topicsList = overlay.querySelector('.lm-topics-list');
            if (topicsList && Array.isArray(programData.topics)) {
                topicsList.innerHTML = generateTopicsListHtml(programData.topics);
            }
        }
    }

    /**
     * Get the display title for a topic, using backend data or fallback
     * @param {Object} topic - Topic object from API
     * @param {number} index - Topic index for fallback numbering
     * @returns {string} Topic title to display
     */
    function getTopicTitle(topic, index) {
        return topic.title || `Chuyên đề ${index + 1}`;
    }

    /**
     * Generate HTML for displaying program topics list
     * @param {Array} topics - Array of topic objects with title property
     * @returns {string} HTML string for topics list
     */
    function generateTopicsListHtml(topics) {
        if (!topics || topics.length === 0) {
            return '<div class="lm-no-topics">Chưa có chuyên đề nào</div>';
        }
        
        return topics.map((topic, index) => {
            const topicTitle = getTopicTitle(topic, index);
            return `<div class="lm-topic-item">
                <span class="lm-topic-number">${index + 1}.</span>
                <span class="lm-topic-title">${escapeHtml(topicTitle)}</span>
            </div>`;
        }).join('');
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
        
        // console.log('viewCourseDetails: courseId=', courseId);
        // console.log('viewCourseDetails: found course from DOM=', course);

        // If we have cached course data and it already contains any of the "detail" fields,
        // AND it has units/topics, just show the modal without an API fetch.
        // If no units, we should fetch from API to get complete course structure.
        if (course && (course.online_course_link || course.instructor || course.estimated_hours || course.course_type || course.course_level)) {
            if (course.units && course.units.length > 0) {
                console.log('viewCourseDetails: using cached course data with units');
                showCourseDetailsModal(course);
                return;
            } else {
                console.log('viewCourseDetails: cached course has no units, fetching from API');
                // Fall through to API fetch to get units
            }
        }

            // Otherwise fetch fresh data from API
            if (course) {
                // fall through to API fetch to get full details
            }// Try to fetch from API
            fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(apiCourse => {
                // Merge cached course data (which has correct course_type from DOM) with API data (which has units)
                const mergedCourse = course ? { ...course, ...apiCourse } : apiCourse;
                console.log('viewCourseDetails: merged course data:', mergedCourse);
                showCourseDetailsModal(mergedCourse);
            })
            .catch(err => {
                console.error('Failed to load course details:', err);
                // Fallback: use cached course if available, or show basic modal
                if (course) {
                    console.log('API failed, using cached course data');
                    showCourseDetailsModal(course);
                } else {
                    showCourseDetailsModal({
                        id: courseId,
                        title: 'Khóa học',
                        short_description: 'Đang tải thông tin...',
                        units: [],
                        course_type: 'Chưa phân loại'
                    });
                }
            });
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
                
                // Extract ID from meta text — allow non-numeric course identifiers (course_key strings)
                // Match ID: <identifier> optionally followed by ' •'
                const idMatch = meta.match(/ID:\s*([^•\n]+)/);
                const idValue = idMatch ? idMatch[1].trim() : null;
                
                // Read any stored dataset fields (new fields added to cards) - declare these first
                const onlineLink = card.dataset.onlineCourseLink || '';
                const instructor = card.dataset.instructor || '';
                // Prefer course_type stored on the DOM dataset (set when rendering/updating cards)
                const courseTypeFromDataset = card.dataset.courseType || '';
                const courseLevel = card.dataset.courseLevel || '';
                
                // meta format: "ID: <id> • <course_type> • <course_level>" (course_type/level optional)
                const metaParts = meta.split('•').map(p => p.trim()).filter(Boolean);
                // metaParts[0] will usually be like 'ID: <id>' so course_type, course_level are subsequent parts
                const courseTypeFromMeta = metaParts.length >= 2 ? metaParts[1] : null;
                const courseLevelFromMeta = metaParts.length >= 3 ? metaParts[2] : null;
                
                // Debug: log meta parsing (commented out for cleaner output)
                // console.log('getAllCoursesFromDOM meta parsing:', {
                //     title,
                //     meta,
                //     metaParts,
                //     courseTypeFromDataset,
                //     courseTypeFromMeta,
                //     courseLevelFromMeta,
                //     idValue
                // });
                const estimatedHours = (card.dataset.estimatedHours !== undefined && card.dataset.estimatedHours !== '')
                    ? card.dataset.estimatedHours
                    : null;

                if (idValue) {
                    courses.push({
                        id: idValue,
                        course_key: card.dataset.courseKey || idValue,
                        title: title,
                        short_description: desc === 'Chưa có mô tả' ? '' : desc,
                        course_type: courseTypeFromDataset || courseTypeFromMeta || '',
                        course_level: courseLevel || courseLevelFromMeta || '',
                        units: [], // Initialize empty units array
                        online_course_link: onlineLink,
                        instructor: instructor,
                        estimated_hours: estimatedHours
                    });
                }
            }
        });
        
        return courses;
    }

    function showCourseDetailsModal(course) {
        ensureDetailModalStyles();
        
        // Debug: Log course object when needed (commented for cleaner output)
        // console.log('showCourseDetailsModal called with course:', course);
        
        // Defensive normalization: prefer explicit course_type, then dataset-style courseType,
        // then attempt to pull from a meta-like string if present. Trim to remove stray whitespace.
        const rawCourseType = (course && (course.course_type || course.courseType || course.type)) || '';
        const normalizedCourseType = (typeof rawCourseType === 'string') ? rawCourseType.trim() : '';
        
        // Debug: log the course type processing (commented for cleaner output)
        // console.log('Course type processing:', {
        //     rawCourseType,
        //     normalizedCourseType,
        //     course_type: course && course.course_type,
        //     courseType: course && course.courseType
        // });
        
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
                                        <span class="lm-detail-value">${course.id || course.course_key || ''}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Loại khóa học:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.course_type || course.courseType || course.type || normalizedCourseType || 'Chưa phân loại')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Mô tả:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.short_description || 'Chưa có mô tả')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Trình độ:</span>
                                        <span class="lm-detail-value">${escapeHtml(
                                            course.course_level === 'basic' ? 'Cơ bản' :
                                            course.course_level === 'intermediate' ? 'Trung cấp' :
                                            course.course_level === 'advanced' ? 'Nâng cao' :
                                            course.course_level || 'Chưa xác định'
                                        )}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Thời lượng ước tính:</span>
                                        <span class="lm-detail-value">${course.estimated_hours !== undefined && course.estimated_hours !== null ? escapeHtml(String(course.estimated_hours)) + ' giờ' : escapeHtml(course.duration || 'Chưa xác định')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Liên kết lớp học trực tuyến:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.online_course_link || 'Chưa có')}</span>
                                    </div>
                                    <div class="lm-detail-row">
                                        <span class="lm-detail-label">Chỉ định giảng viên:</span>
                                        <span class="lm-detail-value">${escapeHtml(course.instructor || 'Chưa có')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="lm-detail-section">
                                <h4>Chuyên đề</h4>
                                <div class="lm-detail-units">
                                    ${course.units && course.units.length > 0 
                                        ? course.units.map(unit => `
                                            <div class="lm-detail-unit">
                                                <h5>${escapeHtml(unit.title || unit.name || 'Chuyên đề')}</h5>
                                                <p>${escapeHtml(unit.description || 'Chưa có mô tả')}</p>
                                            </div>
                                        `).join('')
                                        : '<p class="lm-detail-empty">Chưa có chuyên đề nào</p>'
                                    }
                                </div>
                            </div>

                            <div class="lm-detail-section">
                                <h4>Kiểm tra cuối khoá</h4>
                                <div id="final-eval-area">
                                    <div id="final-eval-loading">Đang tải thông tin kiểm tra cuối khoá...</div>
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

        // Final evaluation: fetch evaluation info and render UI
        (function loadFinalEvaluation() {
            const finalArea = overlay.querySelector('#final-eval-area');
            if (!finalArea) return;
            finalArea.innerHTML = '<div id="final-eval-loading">Đang tải thông tin kiểm tra cuối khoá...</div>';

            fetch(`/api/chalix/dashboard/evaluation/get/${course.id || course.course_key}/`, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' }
            })
            .then(resp => resp.json())
            .then(data => {
                if (!data || !data.success) {
                    finalArea.innerHTML = '<div class="lm-no-topics">Chưa có kiểm tra cuối khoá</div>';
                    return;
                }
                const evalInfo = data.evaluation || {};
                // Render UI depending on evaluation_type
                if (evalInfo.evaluation_type === 'practical') {
                    finalArea.innerHTML = `
                        <div>
                            <div style="margin-bottom:8px;font-weight:600;">Câu hỏi giảng viên:</div>
                            <div id="practical-question-display" style="background:#f8fafc;padding:12px;border-radius:6px;border:1px solid #e5e7eb;">${escapeHtml(evalInfo.practical_question || '—')}</div>
                            <button class="lm-btn secondary" id="edit-practical-btn" style="margin-top:8px;">Chỉnh sửa câu hỏi</button>
                            <div id="practical-edit-area" style="display:none;margin-top:8px;"></div>
                        </div>
                    `;
                    const editBtn = finalArea.querySelector('#edit-practical-btn');
                    const display = finalArea.querySelector('#practical-question-display');
                    const editArea = finalArea.querySelector('#practical-edit-area');

                    editBtn.addEventListener('click', () => {
                        editArea.style.display = 'block';
                        editArea.innerHTML = `
                            <textarea id="practical-question-input" style="width:100%;min-height:120px;" class="lm-form-input">${escapeHtml(evalInfo.practical_question || '')}</textarea>
                            <div style="margin-top:8px;display:flex;gap:8px;justify-content:flex-end;">
                                <button class="lm-btn secondary" id="cancel-practical-btn">Hủy</button>
                                <button class="lm-btn primary" id="save-practical-btn">Lưu câu hỏi</button>
                            </div>
                        `;
                        editArea.querySelector('#cancel-practical-btn').addEventListener('click', () => { editArea.style.display = 'none'; });
                        editArea.querySelector('#save-practical-btn').addEventListener('click', () => {
                            const val = editArea.querySelector('#practical-question-input').value;
                            finalArea.querySelector('#save-practical-btn').disabled = true;
                            fetch(`/api/chalix/dashboard/evaluation/update/${course.id || course.course_key}/`, {
                                method: 'POST',
                                credentials: 'same-origin',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: JSON.stringify({ practical_question: val })
                            })
                            .then(r => r.json())
                            .then(res => {
                                if (res && res.success) {
                                    display.textContent = val;
                                    editArea.style.display = 'none';
                                } else {
                                    alert('Không thể lưu câu hỏi: ' + (res && res.error ? res.error : 'Lỗi server'));
                                }
                            })
                            .catch(e => { console.error(e); alert('Lỗi khi lưu câu hỏi'); })
                            .finally(() => { finalArea.querySelector('#save-practical-btn').disabled = false; });
                        });
                    });
                } else if (evalInfo.evaluation_type === 'quiz') {
                    finalArea.innerHTML = `
                        <div>
                            <div style="margin-bottom:8px;font-weight:600;">Bộ đề trắc nghiệm</div>
                            <div id="quiz-file-info">${evalInfo.has_quiz_file ? escapeHtml(evalInfo.quiz_file_name || '') : 'Chưa tải file'}</div>
                            <div style="margin-top:8px;display:flex;gap:8px;justify-content:flex-end;">
                                <label class="lm-btn secondary" style="cursor:pointer;">
                                    Tải file
                                    <input type="file" id="quiz-file-input" accept=".xlsx,.xls" style="display:none;">
                                </label>
                                <button class="lm-btn primary" id="preview-quiz-btn">Xem trước</button>
                            </div>
                            <div id="quiz-preview-area" style="margin-top:12px;"></div>
                        </div>
                    `;
                    const fileInput = finalArea.querySelector('#quiz-file-input');
                    const previewBtn = finalArea.querySelector('#preview-quiz-btn');
                    const fileInfo = finalArea.querySelector('#quiz-file-info');
                    const previewArea = finalArea.querySelector('#quiz-preview-area');

                    fileInput.addEventListener('change', (e) => {
                        const file = e.target.files[0];
                        if (!file) return;
                        const fd = new FormData();
                        fd.append('quiz_file', file);
                        fetch(`/api/chalix/dashboard/evaluation/upload-quiz/${course.id || course.course_key}/`, {
                            method: 'POST',
                            credentials: 'same-origin',
                            headers: { 'X-CSRFToken': getCookie('csrftoken') },
                            body: fd
                        })
                        .then(r => r.json())
                        .then(res => {
                            if (res && res.success) {
                                fileInfo.textContent = file.name;
                                alert('Tải file thành công.');
                            } else {
                                alert('Tải file thất bại: ' + (res && res.error ? res.error : 'Lỗi'));
                            }
                        })
                        .catch(err => { console.error(err); alert('Lỗi tải file'); });
                    });

                    previewBtn.addEventListener('click', () => {
                        previewArea.innerHTML = 'Đang tải câu hỏi...';
                        fetch(`/api/chalix/dashboard/evaluation/preview-quiz/${course.id || course.course_key}/`, {
                            credentials: 'same-origin',
                            headers: { 'Accept': 'application/json' }
                        })
                        .then(r => r.json())
                        .then(res => {
                            if (res && res.success) {
                                const questions = res.questions || [];
                                if (questions.length === 0) {
                                    previewArea.innerHTML = '<div class="lm-no-topics">Không có câu hỏi</div>';
                                    return;
                                }
                                previewArea.innerHTML = questions.map((q, idx) => `
                                    <div style="border-bottom:1px solid #e5e7eb;padding:8px 0;">
                                        <div style="font-weight:600;">${idx+1}. ${escapeHtml(q.question)}</div>
                                        <div style="margin-top:6px;">${q.choices.map(c => `<div>- ${escapeHtml(c.text)}</div>`).join('')}</div>
                                    </div>
                                `).join('');
                            } else {
                                previewArea.innerHTML = '<div class="lm-no-topics">Không thể tải câu hỏi</div>';
                            }
                        })
                        .catch(err => { console.error(err); previewArea.innerHTML = '<div class="lm-no-topics">Lỗi khi tải câu hỏi</div>'; });
                    });
                } else {
                    finalArea.innerHTML = '<div class="lm-no-topics">Chưa có kiểm tra cuối khoá</div>';
                }
            })
            .catch(err => {
                console.error('Failed to load final evaluation:', err);
                finalArea.innerHTML = '<div class="lm-no-topics">Không thể tải thông tin kiểm tra cuối khoá</div>';
            });
        })();
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
                                <select id="course-level" name="course_level" class="lm-form-input">
                                    <option value="">Chọn trình độ</option>
                                    <option value="Cơ bản" ${course.course_level === 'Cơ bản' ? 'selected' : ''}>Cơ bản</option>
                                    <option value="Nâng cao" ${course.course_level === 'Nâng cao' ? 'selected' : ''}>Nâng cao</option>
                                    <option value="Chuyên ngành" ${course.course_level === 'Chuyên ngành' ? 'selected' : ''}>Chuyên ngành</option>
                                    <option value="Chuyên sâu" ${course.course_level === 'Chuyên sâu' ? 'selected' : ''}>Chuyên sâu</option>
                                </select>
                            </div>
                        </div>

                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-estimated-hours">Thời lượng ước tính (giờ)</label>
                            <input type="number" min="0" id="course-estimated-hours" name="estimated_hours" class="lm-form-input"
                                   value="${escapeHtml(course.estimated_hours !== undefined && course.estimated_hours !== null ? String(course.estimated_hours) : '')}"
                                   placeholder="Số giờ (ví dụ: 40)">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-online-link">Liên kết lớp học trực tuyến</label>
                            <input type="text" id="course-online-link" name="online_course_link" class="lm-form-input"
                                   value="${escapeHtml(course.online_course_link || course.onlineCourseLink || '')}"
                                   placeholder="https://...">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-instructor">Chỉ định giảng viên</label>
                            <input type="text" id="course-instructor" name="instructor" class="lm-form-input"
                                   value="${escapeHtml(course.instructor || '')}"
                                   placeholder="Số điện thoại hoặc Email giảng viên">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="course-description">Mô tả ngắn</label>
                            <textarea id="course-description" name="short_description" 
                                      class="lm-form-input lm-form-textarea" 
                                      placeholder="Mô tả ngắn gọn về khóa học...">${escapeHtml(course.short_description || '')}</textarea>
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label">Chuyên đề</label>
                            <div class="lm-topics-editor" id="units-editor">
                                <div id="units-list">
                                    ${(course.units || []).map((unit, index) => `
                                        <div class="lm-edit-topic-item" data-index="${index}">
                                            <input type="text" class="lm-topic-input" 
                                                   value="${escapeHtml(unit.title || unit.name || '')}" 
                                                   placeholder="Tên chuyên đề">
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
                       value="" placeholder="Tên chuyên đề">
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
            course_key: (originalCourse.course_key || originalCourse.courseKey || originalCourse.courseKeyString || null),
            title: formData.get('title'),
            short_description: formData.get('short_description'),
            course_type: formData.get('course_type'),
            course_level: formData.get('course_level'),
            duration: formData.get('duration'),
            estimated_hours: formData.get('estimated_hours') ? Number(formData.get('estimated_hours')) : null,
            online_course_link: formData.get('online_course_link') || '',
            instructor: formData.get('instructor') || '',
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

            // Use the server response to update the DOM immediately
            try {
                const updated = {
                    id: result.local_course_id || result.id || courseData.id || result.course_key || null,
                    course_key: result.course_key || courseData.course_key || null,
                    title: result.title || courseData.title,
                    short_description: result.short_description || courseData.short_description,
                    online_course_link: result.online_course_link !== undefined ? result.online_course_link : (courseData.online_course_link || ''),
                    instructor: result.instructor !== undefined ? result.instructor : (courseData.instructor || ''),
                    estimated_hours: result.estimated_hours !== undefined ? result.estimated_hours : (courseData.estimated_hours || null)
                };
                updateCourseInDOM(updated);

                // Close overlay then immediately open details modal with fresh data
                setTimeout(() => {
                    try {
                        document.body.removeChild(overlay);
                    } catch (e) { /* ignore */ }

                    // Build a course object suitable for showCourseDetailsModal
                    const detailCourse = Object.assign({}, updated, {
                        title: updated.title,
                        short_description: updated.short_description,
                        course_type: courseData.course_type || '',
                        level: courseData.level || '',
                        duration: courseData.duration || '',
                        units: courseData.units || []
                    });

                    // Open details modal so user sees updated fields immediately
                    try { showCourseDetailsModal(detailCourse); } catch (e) { console.warn('Failed to open details modal', e); }

                    if (onSuccess) onSuccess();
                }, 600);
            } catch (e) {
                console.warn('Failed to apply server response to DOM', e);
                setTimeout(() => {
                    try { document.body.removeChild(overlay); } catch (er) {}
                    if (onSuccess) onSuccess();
                }, 1200);
            }
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

    // Consolidated: Use React modal for course creation
    // ...existing code...

    function openCreateProgramModal(onSuccess) {
        console.log('Opening create program modal with evaluation section');
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

                        <div class="lm-form-group" style="margin-top: 24px;">
                            <label class="lm-form-label" style="color: #1e1e1e; font-weight: 500; font-size: 16px; margin-bottom: 16px; display: block;">Hình thức kiểm tra cuối khoá</label>
                            <div style="display: flex; align-items: center; gap: 16px;">
                                <span id="practical-option" style="color: #1e1e1e; font-size: 16px; font-family: 'Inter', sans-serif; padding: 8px 12px; border-radius: 6px; background-color: #e3f2fd; transition: background-color 0.3s;">Nộp bài thu hoạch</span>
                                <div class="evaluation-switch" style="position: relative; width: 40px; height: 24px;">
                                    <input type="checkbox" id="evaluation-mode-switch" name="evaluation_mode" checked style="opacity: 0; width: 0; height: 0;">
                                    <span class="switch-slider" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #3494c8; transition: .4s; border-radius: 24px;">
                                        <span class="switch-knob" style="position: absolute; content: ''; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; transform: translateX(16px);"></span>
                                    </span>
                                </div>
                                <span id="quiz-option" style="color: #666; font-size: 16px; font-family: 'Inter', sans-serif; padding: 8px 12px; border-radius: 6px; background-color: transparent; transition: background-color 0.3s;">Làm bài trắc nghiệm</span>
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
                            <small class="lm-form-help">Các chuyên đề sẽ được tạo từ các chuyên đề của chương trình</small>
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
                                <select id="new-course-level" name="course_level" class="lm-form-input">
                                    <option value="">Chọn trình độ</option>
                                    <option value="Cơ bản">Cơ bản</option>
                                    <option value="Nâng cao">Nâng cao</option> 
                                    <option value="Chuyên ngành">Chuyên ngành</option>
                                    <option value="Chuyên sâu">Chuyên sâu</option>
                                </select>
                            </div>
                        </div>

                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-estimated-hours">Thời lượng ước tính (giờ)</label>
                            <input type="number" min="0" id="new-course-estimated-hours" name="estimated_hours" class="lm-form-input"
                                   placeholder="Số giờ (ví dụ: 40)">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-online-link">Liên kết lớp học trực tuyến</label>
                            <input type="text" id="new-course-online-link" name="online_course_link" class="lm-form-input"
                                   placeholder="https://...">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-instructor">Chỉ định giảng viên</label>
                            <input type="text" id="new-course-instructor" name="instructor" class="lm-form-input"
                                   placeholder="Tên giảng viên">
                        </div>
                        
                        <div class="lm-form-group">
                            <label class="lm-form-label" for="new-course-description">Mô tả ngắn</label>
                            <textarea id="new-course-description" name="short_description" 
                                      class="lm-form-input lm-form-textarea" 
                                      placeholder="Mô tả ngắn gọn về khóa học..."></textarea>
                        </div>
                        
                        <div class="lm-form-group" id="manual-units" style="display: none;">
                            <label class="lm-form-label">Chuyên đề</label>
                            <div class="lm-topics-editor" id="new-units-editor">
                                <div id="new-units-list">
                                </div>
                                <button type="button" class="lm-add-topic-btn" id="add-new-unit-btn">+ Thêm đơn vị</button>
                            </div>
                        </div>
                        
                        <div class="lm-form-group" id="program-units-preview" style="display: none;">
                            <label class="lm-form-label">Chuyên đề sẽ được tạo</label>
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
                       value="" placeholder="Tên chuyên đề">
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

        // Setup evaluation mode switch
        const evaluationSwitch = overlay.querySelector('#evaluation-mode-switch');
        const practicalOption = overlay.querySelector('#practical-option');
        const quizOption = overlay.querySelector('#quiz-option');
        const slider = overlay.querySelector('.switch-slider');
        const knob = overlay.querySelector('.switch-knob');
        
        // Function to update UI based on switch state
        const updateEvaluationMode = (isPractical) => {
            if (isPractical) {
                // ON = Nộp bài thu hoạch selected
                practicalOption.style.backgroundColor = '#e3f2fd';
                practicalOption.style.color = '#1e1e1e';
                practicalOption.style.fontWeight = '500';
                
                quizOption.style.backgroundColor = 'transparent';
                quizOption.style.color = '#666';
                quizOption.style.fontWeight = '400';
                
                slider.style.backgroundColor = '#3494c8';
                knob.style.transform = 'translateX(16px)';
            } else {
                // OFF = Làm bài trắc nghiệm selected
                practicalOption.style.backgroundColor = 'transparent';
                practicalOption.style.color = '#666';
                practicalOption.style.fontWeight = '400';
                
                quizOption.style.backgroundColor = '#e3f2fd';
                quizOption.style.color = '#1e1e1e';
                quizOption.style.fontWeight = '500';
                
                slider.style.backgroundColor = '#ccc';
                knob.style.transform = 'translateX(0px)';
            }
        };
        
        // Set initial state (ON by default = practical mode)
        updateEvaluationMode(evaluationSwitch.checked);
        
        // Handle switch toggle
        slider.addEventListener('click', () => {
            evaluationSwitch.checked = !evaluationSwitch.checked;
            updateEvaluationMode(evaluationSwitch.checked);
        });
        
        // Also allow clicking on the text options to toggle
        practicalOption.addEventListener('click', () => {
            if (!evaluationSwitch.checked) {
                evaluationSwitch.checked = true;
                updateEvaluationMode(true);
            }
        });
        
        quizOption.addEventListener('click', () => {
            if (evaluationSwitch.checked) {
                evaluationSwitch.checked = false;
                updateEvaluationMode(false);
            }
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

            // Get evaluation mode (single switch)
            const isPracticalMode = overlay.querySelector('#evaluation-mode-switch').checked;
            
            const payload = {
                title: title.trim(),
                short_description: short_description.trim(),
                icon: icon,
                topics: topics,
                allow_practical_submission: isPracticalMode,  // ON = practical, OFF = multiple choice
                allow_multiple_choice: !isPracticalMode      // Opposite of practical
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
        
        // Always try to fetch fresh data from API first for course creation
        selectElement.innerHTML = '<option value="">Đang tải danh sách chương trình...</option>';
        
        fetch('/api/chalix/dashboard/list-programs/', {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'  // Ensure fresh data
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const programs = data.programs || [];
            console.log('[LM] Loaded programs for selection:', programs.map(p => ({id: p.id, title: p.title, topics_count: p.topics_count, topics_length: p.topics?.length || 0})));
            populateProgramsSelect(selectElement, programs);
        })
        .catch(err => {
            console.error('Failed to load programs for selection:', err);
            
            // Fallback to DOM data if API fails
            const existingPrograms = getAllProgramsFromDOM();
            if (existingPrograms.length > 0) {
                console.log('[LM] Using DOM fallback for programs selection');
                populateProgramsSelect(selectElement, existingPrograms);
            } else {
                selectElement.innerHTML = '<option value="">Không thể tải danh sách chương trình</option>';
            }
        });
    }

    function populateProgramsSelect(selectElement, programs) {
        selectElement.innerHTML = '<option value="">Chọn chương trình học...</option>';
        programs.forEach(program => {
            const option = document.createElement('option');
            option.value = program.id;
            
            // Use topics_count from API first, then fallback to topics.length, then extract from DOM
            let topicCount = 0;
            if (program.topics_count !== undefined && program.topics_count !== null) {
                topicCount = program.topics_count;
            } else if (program.topics && Array.isArray(program.topics)) {
                topicCount = program.topics.length;
            } else {
                // Last resort: try to extract from DOM if this program came from getAllProgramsFromDOM
                const card = document.querySelector(`[data-action="view-program"][data-id="${program.id}"]`)?.closest('.lm-card-item');
                if (card) {
                    const metaEl = card.querySelector('.lm-card-meta');
                    if (metaEl) {
                        const topicsMatch = metaEl.textContent.match(/(\d+)\s*chuyên đề/);
                        topicCount = topicsMatch ? parseInt(topicsMatch[1]) : 0;
                    }
                }
            }
            
            option.textContent = `${program.title} (${topicCount} chuyên đề)`;
            selectElement.appendChild(option);
        });
    }

    function showProgramUnitsPreview(programId, previewElement) {
        if (!previewElement) return;
        
        previewElement.innerHTML = '<p class="lm-loading">Đang tải chi tiết chương trình...</p>';
        
        // Always fetch fresh program details from API to ensure we get topics
        fetch(`/api/chalix/dashboard/program-detail/${programId}/`, {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'  // Ensure fresh data
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(program => {
            console.log('[LM] Loaded program for preview:', {id: program.id, title: program.title, topics_count: program.topics_count, topics: program.topics});
            renderUnitsPreview(previewElement, program);
        })
        .catch(err => {
            console.error('Failed to load program details:', err);
            
            // Fallback to DOM data
            const existingPrograms = getAllProgramsFromDOM();
            const program = existingPrograms.find(p => p.id == programId);
            
            if (program) {
                console.log('[LM] Using DOM fallback for program preview:', program);
                renderUnitsPreview(previewElement, program);
            } else {
                previewElement.innerHTML = '<p class="lm-error">Không thể tải chi tiết chương trình</p>';
            }
        });
    }

    function renderUnitsPreview(previewElement, program) {
        console.log('[LM] Rendering units preview for program:', program);
        
        if (!program.topics || program.topics.length === 0) {
            previewElement.innerHTML = '<p class="lm-detail-empty">Chương trình này chưa có chuyên đề nào</p>';
            return;
        }
        
        const unitsHtml = program.topics.map((topic, index) => {
            const topicTitle = getTopicTitle(topic, index);
            return `
            <div class="lm-unit-preview-item">
                <strong>Đơn vị ${index + 1}:</strong> ${escapeHtml(topicTitle)}
                ${topic.description ? `<br><small>${escapeHtml(topic.description)}</small>` : ''}
            </div>`;
        }).join('');
        
        previewElement.innerHTML = `
            <div class="lm-units-preview-list">
                ${unitsHtml}
            </div>
            <p class="lm-preview-note">
                <strong>Lưu ý:</strong> Mỗi chuyên đề sẽ trở thành một chuyên đề trong khóa học mới
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
            course_level: formData.get('course_level'),
            duration: formData.get('duration'),
            estimated_hours: formData.get('estimated_hours') ? Number(formData.get('estimated_hours')) : null,
            online_course_link: formData.get('online_course_link') || '',
            instructor: formData.get('instructor') || '',
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
            courseData.template_program_id = sourceProgramId;
            
            // Get program details to create units - always fetch fresh data
            fetch(`/api/chalix/dashboard/program-detail/${sourceProgramId}/`, {
                credentials: 'same-origin',
                headers: { 
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            })
            .then(sourceProgram => {
                console.log('[LM] Using program for course creation:', {id: sourceProgram.id, title: sourceProgram.title, topics: sourceProgram.topics});
                
                if (sourceProgram && sourceProgram.topics) {
                    courseData.units = sourceProgram.topics.map((topic, index) => {
                        const topicTitle = getTopicTitle(topic, index);
                        return {
                            title: topicTitle,
                            name: topicTitle,
                            description: topic.description || `Chuyên đề được tạo từ chuyên đề "${topicTitle}"`,
                            order: index,
                            source_topic: topic
                        };
                    });
                }
                
                // Determine final_evaluation_type from program settings
                let finalEvaluationType = '';
                if (sourceProgram.allow_practical_submission && sourceProgram.allow_multiple_choice) {
                    // If both are allowed, default to quiz (can be changed later by instructor)
                    finalEvaluationType = 'quiz';
                } else if (sourceProgram.allow_practical_submission) {
                    finalEvaluationType = 'project';
                } else if (sourceProgram.allow_multiple_choice) {
                    finalEvaluationType = 'quiz';
                } else {
                    // Default to project if neither is explicitly set
                    finalEvaluationType = 'project';
                }
                courseData.final_evaluation_type = finalEvaluationType;
                console.log('[LM] Set final_evaluation_type from program:', finalEvaluationType);
                
                // Now proceed with course creation
                proceedWithCourseCreation(courseData, messageEl, createBtn, overlay, onSuccess);
            })
            .catch(err => {
                console.error('Failed to load program for course creation:', err);
                
                // Fallback to DOM data
                const existingPrograms = getAllProgramsFromDOM();
                const sourceProgram = existingPrograms.find(p => p.id == sourceProgramId);
                
                if (sourceProgram && sourceProgram.topics) {
                    courseData.units = sourceProgram.topics.map((topic, index) => {
                        const topicTitle = getTopicTitle(topic, index);
                        return {
                            title: topicTitle,
                            name: topicTitle,
                            description: topic.description || `Chuyên đề được tạo từ chuyên đề "${topicTitle}"`,
                            order: index,
                            source_topic: topic
                        };
                    });
                    
                    // Set final_evaluation_type from fallback program data (if available)
                    let finalEvaluationType = '';
                    if (sourceProgram.allow_practical_submission && sourceProgram.allow_multiple_choice) {
                        finalEvaluationType = 'quiz';
                    } else if (sourceProgram.allow_practical_submission) {
                        finalEvaluationType = 'project';
                    } else if (sourceProgram.allow_multiple_choice) {
                        finalEvaluationType = 'quiz';
                    } else {
                        finalEvaluationType = 'project';
                    }
                    courseData.final_evaluation_type = finalEvaluationType;
                    console.log('[LM] Set final_evaluation_type from DOM fallback:', finalEvaluationType);
                }
                
                proceedWithCourseCreation(courseData, messageEl, createBtn, overlay, onSuccess);
            });
            return; // Exit early, let the promise chain handle the rest
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
        
        // For manual creation, proceed directly
        proceedWithCourseCreation(courseData, messageEl, createBtn, overlay, onSuccess);
    }

    function proceedWithCourseCreation(courseData, messageEl, createBtn, overlay, onSuccess) {
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
            const creationType = courseData.creation_type;
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