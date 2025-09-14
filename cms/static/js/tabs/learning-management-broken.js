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

    window.CMS_TABS = window.CMS_TABS || {};

    function ensureStyles() {
        if (document.getElementById('cms-learning-management-styles')) return;
        const css = `
            .lm-wrap { display:flex; justify-content:center; padding: 20px 12px 80px; }
            .lm-card { max-width:1200px; width:100%; background: transparent; padding: 40px 12px; text-align:center; }
            .lm-title { font-size:28px; font-weight:700; margin: 80px 0 8px; color:#222; }
            .lm-desc { color:#6b7680; margin: 0 0 32px; font-size:16px; }
            
            /* Subtabs */
            .lm-subtabs { display:flex; justify-content:center; margin-bottom: 32px; border-bottom: 2px solid #e5e7eb; }
            .lm-subtab-btn { 
                background: none; border: none; padding: 16px 32px; font-size: 16px; font-weight: 600; 
                color: #6b7280; cursor: pointer; border-bottom: 3px solid transparent; 
                transition: all 200ms ease; position: relative; top: 2px; 
            }
            .lm-subtab-btn:hover { color: #374151; }
            .lm-subtab-btn.active { color: #1f2937; border-bottom-color: #3b82f6; }
            
            /* Subtab panels */
            .lm-subtab-content { text-align: left; }
            .lm-subtab-panel { display: none; }
            .lm-subtab-panel.active { display: block; }
            
            /* Tab headers */
            .lm-tab-header { 
                display: flex; justify-content: space-between; align-items: center; 
                margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;
            }
            .lm-tab-header h3 { margin: 0; font-size: 24px; font-weight: 700; color: #1f2937; }
            
            /* Buttons */
            .lm-btn { 
                display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; 
                border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; 
                transition: all 200ms ease; text-decoration: none;
            }
            .lm-btn.primary { background: #3b82f6; color: #fff; }
            .lm-btn.primary:hover { background: #2563eb; transform: translateY(-1px); }
            .lm-btn.secondary { background: #6b7280; color: #fff; }
            .lm-btn.secondary:hover { background: #4b5563; }
            .lm-btn-icon { font-size: 16px; font-weight: bold; }
            
            /* Content area */
            .lm-content-area { min-height: 400px; }
            .lm-loading { 
                text-align: center; padding: 40px; color: #6b7280; 
                font-style: italic; font-size: 16px; 
            }
            
            /* Lists */
            .lm-list { display: grid; gap: 16px; }
            .lm-list-item { 
                background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; 
                padding: 20px; transition: all 200ms ease; cursor: pointer;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .lm-list-item:hover { 
                border-color: #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,0.15); 
                transform: translateY(-2px);
            }
            .lm-item-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
            .lm-item-title { 
                font-size: 18px; font-weight: 700; color: #1f2937; margin: 0; 
                display: flex; align-items: center; gap: 12px;
            }
            .lm-item-meta { color: #6b7280; font-size: 14px; }
            .lm-item-description { color: #4b5563; margin: 8px 0; line-height: 1.5; }
            .lm-item-stats { 
                display: flex; gap: 16px; margin-top: 12px; padding-top: 12px; 
                border-top: 1px solid #f3f4f6; font-size: 13px; color: #6b7280;
            }
            .lm-item-actions { display: flex; gap: 8px; opacity: 0.7; transition: opacity 200ms ease; }
            .lm-list-item:hover .lm-item-actions { opacity: 1; }
            .lm-action-btn { 
                background: #f3f4f6; border: none; padding: 6px 12px; border-radius: 6px; 
                font-size: 12px; font-weight: 600; color: #374151; cursor: pointer;
                transition: background-color 150ms ease;
            }
            .lm-action-btn:hover { background: #e5e7eb; }
            .lm-action-btn.edit { background: #dbeafe; color: #1d4ed8; }
            .lm-action-btn.edit:hover { background: #bfdbfe; }
            .lm-action-btn.delete { background: #fecaca; color: #dc2626; }
            .lm-action-btn.delete:hover { background: #fca5a5; }
            
            /* Empty state */
            .lm-empty { 
                text-align: center; padding: 60px 20px; color: #6b7280; 
                background: #f9fafb; border-radius: 12px; border: 2px dashed #d1d5db;
            }
            .lm-empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
            .lm-empty-text { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
            .lm-empty-description { font-size: 14px; }
            
            /* Detail modal styles */
            .lm-detail-modal { max-width: 800px !important; }
            .lm-detail-content { padding: 0; }
            .lm-detail-header { 
                display: flex; justify-content: space-between; align-items: flex-start; 
                margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;
            }
            .lm-detail-title { display: flex; align-items: center; gap: 12px; flex: 1; }
            .lm-detail-title h4 { margin: 0; font-size: 24px; font-weight: 700; color: #1f2937; }
            .lm-detail-actions { display: flex; gap: 8px; }
            .lm-detail-section { margin-bottom: 32px; }
            .lm-detail-section h5 { 
                font-size: 18px; font-weight: 600; color: #374151; 
                margin: 0 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #f3f4f6;
            }
            .lm-detail-grid { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 16px; margin-bottom: 16px;
            }
            .lm-detail-item { display: flex; flex-direction: column; gap: 4px; }
            .lm-detail-item label { font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; }
            .lm-detail-item span { font-size: 14px; color: #1f2937; }
            .lm-description { 
                background: #f8fafc; padding: 16px; border-radius: 8px; 
                border-left: 4px solid #3b82f6; font-size: 14px; color: #374151; line-height: 1.6;
            }
            .lm-topics-list, .lm-units-list { 
                background: #f8fafc; padding: 16px; border-radius: 8px; margin: 0; 
                list-style: none; 
            }
            .lm-topics-list li, .lm-units-list li { 
                padding: 8px 0; border-bottom: 1px solid #e5e7eb; 
                font-size: 14px; color: #374151;
            }
            .lm-topics-list li:last-child, .lm-units-list li:last-child { border-bottom: none; }
            .lm-error { 
                text-align: center; padding: 40px; color: #dc2626; 
                background: #fef2f2; border-radius: 8px; border: 1px solid #fecaca;
            }
            .lm-error-icon { font-size: 32px; margin-bottom: 16px; }
            .lm-error-text { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
            
            /* Program/Course icons */
            .chalix-icon-svg { width: 24px; height: 24px; }
            
            @media (max-width:768px) { 
                .lm-title { font-size: 22px; margin-top: 60px; } 
                .lm-subtabs { overflow-x: auto; }
                .lm-tab-header { flex-direction: column; gap: 16px; align-items: stretch; }
                .lm-list { grid-template-columns: 1fr; }
                .lm-item-header { flex-direction: column; gap: 8px; }
                .lm-detail-grid { grid-template-columns: 1fr; }
                .lm-detail-header { flex-direction: column; gap: 16px; }
            }
        `;
        const style = document.createElement('style');
        style.id = 'cms-learning-management-styles';
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
                    <h2 class="lm-title">${config.contentTitle}</h2>
                    <p class="lm-desc">${config.contentDescription}</p>

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
            console.error('Error loading programs:', err);
            contentArea.innerHTML = `
                <div class="lm-empty">
                    <div class="lm-empty-icon">⚠️</div>
                    <div class="lm-empty-text">Lỗi khi tải danh sách</div>
                    <div class="lm-empty-description">Không thể tải danh sách chương trình học. Vui lòng thử lại.</div>
                </div>
            `;
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
            console.error('Error loading courses:', err);
            contentArea.innerHTML = `
                <div class="lm-empty">
                    <div class="lm-empty-icon">⚠️</div>
                    <div class="lm-empty-text">Lỗi khi tải danh sách</div>
                    <div class="lm-empty-description">Không thể tải danh sách khóa học. Vui lòng thử lại.</div>
                </div>
            `;
        });
    }

    function renderProgramsList(contentArea, programs) {
        if (programs.length === 0) {
            contentArea.innerHTML = `
                <div class="lm-empty">
                    <div class="lm-empty-icon">📚</div>
                    <div class="lm-empty-text">Chưa có chương trình học nào</div>
                    <div class="lm-empty-description">Tạo chương trình học đầu tiên để bắt đầu</div>
                </div>
            `;
            return;
        }

        const listHtml = programs.map(program => {
            const topicsList = (program.topics || []).map(t => escapeHtml(t.title)).join(', ');
            const iconSvg = getIconSvg(program.icon || 'seed-of-life');
            const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';
            
            return `
                <div class="lm-list-item" data-id="${program.id}" data-type="program">
                    <div class="lm-item-header">
                        <h4 class="lm-item-title">
                            ${iconHtml}
                            ${escapeHtml(program.title)}
                        </h4>
                        <div class="lm-item-actions">
                            <button class="lm-action-btn edit" data-action="edit-program" data-id="${program.id}">Chỉnh sửa</button>
                            <button class="lm-action-btn delete" data-action="delete-program" data-id="${program.id}">Xóa</button>
                        </div>
                    </div>
                    <div class="lm-item-description">
                        <strong>Chuyên đề:</strong> ${topicsList || 'Chưa có chuyên đề nào'}
                    </div>
                    <div class="lm-item-stats">
                        <span>📊 ${(program.topics || []).length} chuyên đề</span>
                        <span>⚙️ ${program.update_topics ? 'Tự động cập nhật' : 'Cố định'}</span>
                        <span>👤 ${escapeHtml(program.created_by || 'Không rõ')}</span>
                        <span>📅 ${new Date(program.created_at).toLocaleDateString('vi-VN')}</span>
                    </div>
                </div>
            `;
        }).join('');

        contentArea.innerHTML = `<div class="lm-list">${listHtml}</div>`;
        
        // Add click handlers for items and actions
        contentArea.querySelectorAll('.lm-list-item').forEach(item => {
            // Click on item to view details
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.lm-item-actions')) {
                    const programId = item.dataset.id;
                    viewProgramDetails(programId);
                }
            });
        });

        contentArea.querySelectorAll('.lm-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const id = btn.dataset.id;
                
                if (action === 'edit-program') {
                    editProgram(id);
                } else if (action === 'delete-program') {
                    deleteProgram(id, () => loadProgramsList(contentArea));
                }
            });
        });
    }

    function renderCoursesList(contentArea, courses) {
        if (courses.length === 0) {
            contentArea.innerHTML = `
                <div class="lm-empty">
                    <div class="lm-empty-icon">🎓</div>
                    <div class="lm-empty-text">Chưa có khóa học nào</div>
                    <div class="lm-empty-description">Tạo khóa học đầu tiên để bắt đầu</div>
                </div>
            `;
            return;
        }

        const listHtml = courses.map(course => {
            return `
                <div class="lm-list-item" data-id="${course.id}" data-type="course">
                    <div class="lm-item-header">
                        <h4 class="lm-item-title">
                            🎓 ${escapeHtml(course.title)}
                        </h4>
                        <div class="lm-item-actions">
                            <button class="lm-action-btn edit" data-action="edit-course" data-id="${course.id}">Chỉnh sửa</button>
                            <button class="lm-action-btn delete" data-action="delete-course" data-id="${course.id}">Xóa</button>
                        </div>
                    </div>
                    <div class="lm-item-description">
                        ${escapeHtml(course.short_description || 'Chưa có mô tả')}
                    </div>
                    <div class="lm-item-stats">
                        <span>📝 ${escapeHtml(course.course_type || 'Không rõ loại')}</span>
                        <span>👤 ${escapeHtml(course.created_by || 'Không rõ')}</span>
                        <span>📅 ${new Date(course.created_at).toLocaleDateString('vi-VN')}</span>
                        ${course.template_program_title ? `<span>📋 Mẫu: ${escapeHtml(course.template_program_title)}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        contentArea.innerHTML = `<div class="lm-list">${listHtml}</div>`;
        
        // Add click handlers for items and actions
        contentArea.querySelectorAll('.lm-list-item').forEach(item => {
            // Click on item to view details
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.lm-item-actions')) {
                    const courseId = item.dataset.id;
                    viewCourseDetails(courseId);
                }
            });
        });

        contentArea.querySelectorAll('.lm-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const id = btn.dataset.id;
                
                if (action === 'edit-course') {
                    editCourse(id);
                } else if (action === 'delete-course') {
                    deleteCourse(id, () => loadCoursesList(contentArea));
                }
            });
        });
    }
    function openCreateCourseModal(onSuccess) {
        // create modal elements
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        overlay.innerHTML = `
            <div class="lm-modal">
                <div class="lm-modal-header">
                    <h3>Tạo khóa học mới</h3>
                    <button class="lm-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="lm-modal-body">
                    <label>Tiêu đề khóa học
                        <input type="text" name="title" class="lm-input-title" placeholder="Nhập tiêu đề" />
                    </label>
                    <label>Mô tả ngắn
                        <textarea name="short_description" class="lm-input-desc" placeholder="Mô tả ngắn về khóa học"></textarea>
                    </label>
                    <label>Sử dụng mẫu chương trình
                        <select class="lm-template-type" name="template_type">
                            <option value="">-- Không sử dụng mẫu --</option>
                            <option value="program">Chương trình mẫu</option>
                        </select>
                    </label>
                    <div class="lm-program-select-wrapper" style="display:none; margin-top:12px;">
                        <label>Chọn chương trình mẫu
                            <select class="lm-select-program" name="template_program">
                                <option value="">-- Chọn chương trình --</option>
                            </select>
                        </label>
                        <div class="lm-program-preview" style="display:none; margin-top:12px; padding:12px; background:#f8fafc; border-radius:8px; border-left:4px solid #3b82f6;">
                            <h4 style="margin:0 0 8px; font-size:14px; font-weight:600; color:#374151;">Xem trước chương trình:</h4>
                            <div class="lm-program-info"></div>
                            <div style="margin-top:12px; font-size:12px; color:#6b7280;">
                                ℹ️ Khi tạo khóa học, các chuyên đề sẽ được chuyển thành đơn vị học tập (units) tương ứng.
                            </div>
                        </div>
                    </div>
                    <label>Loại khóa học
                        <select class="lm-select-type" name="course_type">
                            <option value="bat-buoc">bắt buộc</option>
                            <option value="tuy-chon">tuỳ chọn</option>
                            <option value="co-quan">khóa học của cơ quan</option>
                        </select>
                    </label>
                    <div class="lm-modal-actions">
                        <button class="lm-btn primary lm-submit">Tạo</button>
                        <button class="lm-btn secondary lm-cancel">Hủy</button>
                    </div>
                    <div class="lm-modal-msg" aria-live="polite"></div>
                </div>
            </div>
        `;

        ensureModalStyles();

        document.body.appendChild(overlay);

        const closeModal = () => {
            overlay.remove();
        };

        overlay.querySelector('.lm-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.lm-cancel').addEventListener('click', closeModal);

        const submitBtn = overlay.querySelector('.lm-submit');
        const msgBox = overlay.querySelector('.lm-modal-msg');
        // populate program-select (used when template type = 'program')
        const templateTypeSelect = overlay.querySelector('.lm-template-type');
        const programSelectWrapper = overlay.querySelector('.lm-program-select-wrapper');
        const programSelect = overlay.querySelector('.lm-select-program');
        const programPreview = overlay.querySelector('.lm-program-preview');
        const programInfo = overlay.querySelector('.lm-program-info');

        // Load programs and populate select
        (function loadPrograms() {
            fetch('/api/chalix/dashboard/list-programs/', { credentials: 'same-origin', headers: { 'Accept': 'application/json' }})
                .then(r => { if (!r.ok) throw r; return r.json(); })
                .then(data => {
                    const programs = data.programs || [];
                    programSelect.innerHTML = '<option value="">-- Chọn chương trình --</option>';
                    for (const p of programs) {
                        const opt = document.createElement('option');
                        opt.value = p.id;
                        opt.textContent = p.title;
                        opt.dataset.programData = JSON.stringify(p);
                        programSelect.appendChild(opt);
                    }
                }).catch(() => {
                    // keep default option if load fails
                    console.warn('Failed to load programs for course creation');
                });
        })();

        // show/hide program select when template type changes
        templateTypeSelect.addEventListener('change', () => {
            if (templateTypeSelect.value === 'program') {
                programSelectWrapper.style.display = '';
            } else {
                programSelectWrapper.style.display = 'none';
                programSelect.value = '';
                programPreview.style.display = 'none';
            }
        });

        // Show program preview when program is selected
        programSelect.addEventListener('change', () => {
            if (programSelect.value) {
                const selectedOption = programSelect.querySelector(`option[value="${programSelect.value}"]`);
                if (selectedOption && selectedOption.dataset.programData) {
                    try {
                        const program = JSON.parse(selectedOption.dataset.programData);
                        const iconSvg = getIconSvg(program.icon || 'seed-of-life');
                        const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';
                        const topicsList = (program.topics || []).map((t, index) => 
                            `<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                                <span style="font-size:12px; color:#6b7280;">Unit ${index + 1}:</span>
                                <span style="font-size:13px; color:#374151;">${escapeHtml(t.title)}</span>
                            </div>`
                        ).join('');

                        programInfo.innerHTML = `
                            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                                ${iconHtml}
                                <strong style="color:#1f2937;">${escapeHtml(program.title)}</strong>
                            </div>
                            <div style="font-size:12px; color:#6b7280; margin-bottom:8px;">
                                ${program.topics ? program.topics.length : 0} chuyên đề sẽ trở thành ${program.topics ? program.topics.length : 0} đơn vị học tập
                            </div>
                            ${topicsList || '<div style="color:#6b7280; font-size:12px;">Chưa có chuyên đề</div>'}
                        `;
                        programPreview.style.display = 'block';
                    } catch (e) {
                        console.warn('Failed to parse program data:', e);
                        programPreview.style.display = 'none';
                    }
                }
            } else {
                programPreview.style.display = 'none';
            }
        });

        submitBtn.addEventListener('click', () => {
            const title = overlay.querySelector('.lm-input-title').value.trim();
            const short_description = overlay.querySelector('.lm-input-desc').value.trim();
            // read selected template program id if present
            let template_program_id = null;
            const programSelectEl = overlay.querySelector('.lm-select-program');
            if (programSelectEl && programSelectEl.value) template_program_id = programSelectEl.value;
            const course_type = (overlay.querySelector('.lm-select-type') && overlay.querySelector('.lm-select-type').value) || null;

            if (!title) {
                msgBox.textContent = 'Tiêu đề bắt buộc';
                msgBox.style.color = '#c23';
                return;
            }

            // Show more detailed message when using template
            const loadingText = template_program_id ? 
                'Đang tạo khóa học và chuyển đổi chuyên đề thành đơn vị học tập...' : 
                'Đang tạo khóa học...';
            msgBox.textContent = loadingText;
            msgBox.style.color = '#6b7280';

            // POST to backend API with enhanced data
            const url = '/api/chalix/dashboard/create-course/';
            const csrftoken = getCookie('csrftoken');

            const requestData = { 
                title: title, 
                short_description: short_description, 
                template_program_id: template_program_id, 
                course_type: course_type 
            };

            // If using template, add flag for unit creation
            if (template_program_id) {
                requestData.create_units_from_topics = true;
            }

            fetch(url, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestData)
            }).then(resp => {
                if (!resp.ok) throw resp;
                return resp.json();
            }).then(data => {
                msgBox.style.color = '#0a7';
                const successText = data.units_created ? 
                    `Tạo thành công! Đã tạo ${data.units_created} đơn vị học tập từ chương trình mẫu.` : 
                    'Tạo thành công!';
                msgBox.textContent = successText;
                
                if (onSuccess) onSuccess();
                setTimeout(closeModal, 1200);
            }).catch(err => {
                err.text && err.text().then(t => { 
                    let errorMsg = 'Lỗi khi tạo khóa học';
                    try {
                        const errorData = JSON.parse(t);
                        errorMsg = errorData.error || errorMsg;
                    } catch (e) {
                        errorMsg = t || errorMsg;
                    }
                    msgBox.textContent = errorMsg; 
                    msgBox.style.color = '#c23'; 
                }).catch(() => { 
                    msgBox.textContent = 'Lỗi khi tạo khóa học'; 
                    msgBox.style.color = '#c23'; 
                });
            });
        });
    }

    function viewProgramDetails(programId) {
        // Create detail modal
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        overlay.innerHTML = `
            <div class="lm-modal lm-detail-modal">
                <div class="lm-modal-header">
                    <h3>Chi tiết chương trình học</h3>
                    <button class="lm-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="lm-modal-body">
                    <div class="lm-loading">Đang tải chi tiết chương trình...</div>
                </div>
            </div>
        `;

        ensureModalStyles();
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.lm-modal-close').addEventListener('click', closeModal);

        // Fetch program details
        fetch(`/api/chalix/dashboard/program-detail/${programId}/`, { 
            credentials: 'same-origin', 
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
        .then(program => {
            const modalBody = overlay.querySelector('.lm-modal-body');
            const topicsList = (program.topics || []).map(t => `<li>${escapeHtml(t.title)}</li>`).join('');
            const iconSvg = getIconSvg(program.icon || 'seed-of-life');
            const iconHtml = iconSvg ? iconSvg.outerHTML : '📚';

            modalBody.innerHTML = `
                <div class="lm-detail-content">
                    <div class="lm-detail-header">
                        <div class="lm-detail-title">
                            ${iconHtml}
                            <h4>${escapeHtml(program.title)}</h4>
                        </div>
                        <div class="lm-detail-actions">
                            <button class="lm-btn secondary" onclick="editProgram(${program.id})">Chỉnh sửa</button>
                        </div>
                    </div>
                    
                    <div class="lm-detail-section">
                        <h5>Thông tin cơ bản</h5>
                        <div class="lm-detail-grid">
                            <div class="lm-detail-item">
                                <label>ID:</label>
                                <span>${program.id}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Biểu tượng:</label>
                                <span>${iconHtml} ${escapeHtml(program.icon || '')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Cập nhật tự động:</label>
                                <span>${program.update_topics ? '✅ Có' : '❌ Không'}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Người tạo:</label>
                                <span>${escapeHtml(program.created_by || 'Không rõ')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Ngày tạo:</label>
                                <span>${new Date(program.created_at).toLocaleString('vi-VN')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Số chuyên đề:</label>
                                <span>${(program.topics || []).length}</span>
                            </div>
                        </div>
                    </div>

                    <div class="lm-detail-section">
                        <h5>Danh sách chuyên đề</h5>
                        ${topicsList ? `<ul class="lm-topics-list">${topicsList}</ul>` : '<p class="lm-empty-text">Chưa có chuyên đề nào</p>'}
                    </div>
                </div>
            `;
        })
        .catch(err => {
            const modalBody = overlay.querySelector('.lm-modal-body');
            modalBody.innerHTML = `
                <div class="lm-error">
                    <div class="lm-error-icon">⚠️</div>
                    <div class="lm-error-text">Không thể tải chi tiết chương trình</div>
                    <button class="lm-btn secondary" onclick="this.closest('.lm-modal-overlay').remove()">Đóng</button>
                </div>
            `;
        });
    }

    function viewCourseDetails(courseId) {
        // Create detail modal
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        overlay.innerHTML = `
            <div class="lm-modal lm-detail-modal">
                <div class="lm-modal-header">
                    <h3>Chi tiết khóa học</h3>
                    <button class="lm-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="lm-modal-body">
                    <div class="lm-loading">Đang tải chi tiết khóa học...</div>
                </div>
            </div>
        `;

        ensureModalStyles();
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.lm-modal-close').addEventListener('click', closeModal);

        // Fetch course details
        fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, { 
            credentials: 'same-origin', 
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
        .then(course => {
            const modalBody = overlay.querySelector('.lm-modal-body');

            modalBody.innerHTML = `
                <div class="lm-detail-content">
                    <div class="lm-detail-header">
                        <div class="lm-detail-title">
                            🎓
                            <h4>${escapeHtml(course.title)}</h4>
                        </div>
                        <div class="lm-detail-actions">
                            <button class="lm-btn secondary" onclick="editCourse(${course.id})">Chỉnh sửa</button>
                        </div>
                    </div>
                    
                    <div class="lm-detail-section">
                        <h5>Thông tin cơ bản</h5>
                        <div class="lm-detail-grid">
                            <div class="lm-detail-item">
                                <label>ID:</label>
                                <span>${course.id}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Loại khóa học:</label>
                                <span>${escapeHtml(course.course_type || 'Không rõ')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Người tạo:</label>
                                <span>${escapeHtml(course.created_by || 'Không rõ')}</span>
                            </div>
                            <div class="lm-detail-item">
                                <label>Ngày tạo:</label>
                                <span>${new Date(course.created_at).toLocaleString('vi-VN')}</span>
                            </div>
                            ${course.template_program_title ? `
                            <div class="lm-detail-item">
                                <label>Chương trình mẫu:</label>
                                <span>${escapeHtml(course.template_program_title)}</span>
                            </div>` : ''}
                        </div>
                    </div>

                    <div class="lm-detail-section">
                        <h5>Mô tả</h5>
                        <div class="lm-description">
                            ${course.short_description ? escapeHtml(course.short_description) : 'Chưa có mô tả'}
                        </div>
                    </div>

                    ${course.units && course.units.length ? `
                    <div class="lm-detail-section">
                        <h5>Đơn vị học tập (${course.units.length})</h5>
                        <ul class="lm-units-list">
                            ${course.units.map(unit => `<li>${escapeHtml(unit.title || unit.name)}</li>`).join('')}
                        </ul>
                    </div>` : ''}
                </div>
            `;
        })
        .catch(err => {
            const modalBody = overlay.querySelector('.lm-modal-body');
            modalBody.innerHTML = `
                <div class="lm-error">
                    <div class="lm-error-icon">⚠️</div>
                    <div class="lm-error-text">Không thể tải chi tiết khóa học</div>
                    <button class="lm-btn secondary" onclick="this.closest('.lm-modal-overlay').remove()">Đóng</button>
                </div>
            `;
        });
    }

    function editProgram(programId) {
        // Close any existing modals first
        const existingModal = document.querySelector('.lm-modal-overlay');
        if (existingModal) existingModal.remove();

        // Create edit modal - similar to create but pre-filled
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        overlay.innerHTML = `
            <div class="chalix-modal">
                <div class="chalix-modal-header">
                    <span class="chalix-modal-title">CHỈNH SỬA CHƯƠNG TRÌNH HỌC</span>
                    <button class="chalix-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="chalix-modal-content">
                    <div class="lm-loading">Đang tải dữ liệu chương trình...</div>
                </div>
                <div class="chalix-modal-buttons" style="display:none;">
                    <button class="chalix-btn-cancel">Hủy</button>
                    <button class="chalix-btn-submit">Cập nhật chương trình học</button>
                </div>
                <div class="chalix-modal-msg" aria-live="polite"></div>
            </div>
        `;

        ensureProgramModalStyles();
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.chalix-modal-close').addEventListener('click', closeModal);

        // Fetch program details and populate form
        fetch(`/api/chalix/dashboard/program-detail/${programId}/`, { 
            credentials: 'same-origin', 
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
        .then(program => {
            const modalContent = overlay.querySelector('.chalix-modal-content');
            const modalButtons = overlay.querySelector('.chalix-modal-buttons');
            
            modalContent.innerHTML = `
                <div class="chalix-form-group">
                    <label class="chalix-form-label">Tiêu đề chương trình học</label>
                    <input type="text" class="chalix-form-input chalix-input-title" placeholder="Nhập tiêu đề chương trình" value="${escapeHtml(program.title)}" />
                </div>

                <div class="chalix-form-group">
                    <label class="chalix-form-label">Ký hiệu</label>
                    <div class="chalix-icon-dropdown-wrapper">
                        <button type="button" class="chalix-icon-dropdown-trigger" aria-haspopup="listbox" aria-expanded="false" data-selected="${program.icon || 'seed-of-life'}">
                            <div class="chalix-selected-icon"></div>
                            <svg class="chalix-dropdown-arrow" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                        <div class="chalix-icon-dropdown-menu" style="display: none;" role="listbox">
                            ${getIconOptionsHtml()}
                        </div>
                    </div>
                </div>

                <div class="chalix-form-group chalix-switch-group">
                    <label class="chalix-switch-label">
                        <input type="checkbox" name="update_topics" class="chalix-switch-input" ${program.update_topics ? 'checked' : ''}>
                        <span class="chalix-switch-slider"></span>
                        <span class="chalix-switch-text">Cập nhật các chuyên đề</span>
                    </label>
                </div>

                <div class="chalix-form-group">
                    <label class="chalix-form-label">Thêm chuyên đề</label>
                    <div class="chalix-topics-list">
                        ${(program.topics || []).map(topic => `
                            <div class="chalix-topic-item">
                                <span class="chalix-topic-text">${escapeHtml(topic.title)}</span>
                                <button type="button" class="chalix-topic-remove" data-action="remove">—</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="chalix-add-topic">+ Thêm mới</button>
                </div>
            `;

            modalButtons.style.display = 'flex';
            
            setupEditProgramModal(overlay, programId);
        })
        .catch(err => {
            const modalContent = overlay.querySelector('.chalix-modal-content');
            modalContent.innerHTML = `
                <div class="lm-error">
                    <div class="lm-error-icon">⚠️</div>
                    <div class="lm-error-text">Không thể tải dữ liệu chương trình</div>
                </div>
            `;
        });
    }

    function editCourse(courseId) {
        // Close any existing modals first
        const existingModal = document.querySelector('.lm-modal-overlay');
        if (existingModal) existingModal.remove();

        // Create edit modal
        const overlay = document.createElement('div');
        overlay.className = 'lm-modal-overlay';
        overlay.innerHTML = `
            <div class="lm-modal">
                <div class="lm-modal-header">
                    <h3>Chỉnh sửa khóa học</h3>
                    <button class="lm-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="lm-modal-body">
                    <div class="lm-loading">Đang tải dữ liệu khóa học...</div>
                </div>
            </div>
        `;

        ensureModalStyles();
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.lm-modal-close').addEventListener('click', closeModal);

        // Fetch course details and populate form
        fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, { 
            credentials: 'same-origin', 
            headers: { 'Accept': 'application/json' }
        })
        .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
        .then(course => {
            const modalBody = overlay.querySelector('.lm-modal-body');
            
            modalBody.innerHTML = `
                <label>Tiêu đề khóa học
                    <input type="text" name="title" class="lm-input-title" placeholder="Nhập tiêu đề" value="${escapeHtml(course.title)}" />
                </label>
                <label>Mô tả ngắn
                    <textarea name="short_description" class="lm-input-desc" placeholder="Mô tả ngắn về khóa học">${escapeHtml(course.short_description || '')}</textarea>
                </label>
                <label>Loại khóa học
                    <select class="lm-select-type" name="course_type">
                        <option value="bat-buoc" ${course.course_type === 'bat-buoc' ? 'selected' : ''}>bắt buộc</option>
                        <option value="tuy-chon" ${course.course_type === 'tuy-chon' ? 'selected' : ''}>tuỳ chọn</option>
                        <option value="co-quan" ${course.course_type === 'co-quan' ? 'selected' : ''}>khóa học của cơ quan</option>
                    </select>
                </label>
                <div class="lm-modal-actions">
                    <button class="lm-btn primary lm-submit">Cập nhật</button>
                    <button class="lm-btn secondary lm-cancel">Hủy</button>
                </div>
                <div class="lm-modal-msg" aria-live="polite"></div>
            `;

            // Setup form handlers
            overlay.querySelector('.lm-cancel').addEventListener('click', closeModal);
            
            const submitBtn = overlay.querySelector('.lm-submit');
            const msgBox = overlay.querySelector('.lm-modal-msg');

            submitBtn.addEventListener('click', () => {
                const title = overlay.querySelector('.lm-input-title').value.trim();
                const short_description = overlay.querySelector('.lm-input-desc').value.trim();
                const course_type = overlay.querySelector('.lm-select-type').value;

                if (!title) {
                    msgBox.textContent = 'Tiêu đề bắt buộc';
                    msgBox.style.color = '#c23';
                    return;
                }

                msgBox.textContent = 'Đang cập nhật...';

                fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, {
                    method: 'PUT',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ title, short_description, course_type })
                }).then(resp => {
                    if (!resp.ok) throw resp;
                    return resp.json();
                }).then(data => {
                    msgBox.style.color = '#0a7';
                    msgBox.textContent = 'Cập nhật thành công';
                    
                    // Refresh the courses list
                    const coursesContent = document.querySelector('#lm-courses-tab .lm-content-area');
                    if (coursesContent) {
                        loadCoursesList(coursesContent);
                    }
                    
                    setTimeout(closeModal, 800);
                }).catch(err => {
                    err.text && err.text().then(t => { 
                        msgBox.textContent = t; 
                        msgBox.style.color = '#c23'; 
                    }).catch(() => { 
                        msgBox.textContent = 'Lỗi khi cập nhật khóa học'; 
                        msgBox.style.color = '#c23'; 
                    });
                });
            });
        })
        .catch(err => {
            const modalBody = overlay.querySelector('.lm-modal-body');
            modalBody.innerHTML = `
                <div class="lm-error">
                    <div class="lm-error-icon">⚠️</div>
                    <div class="lm-error-text">Không thể tải dữ liệu khóa học</div>
                    <button class="lm-btn secondary" onclick="this.closest('.lm-modal-overlay').remove()">Đóng</button>
                </div>
            `;
        });
    }

    function deleteProgram(programId, onSuccess) {
        if (!confirm('Bạn có chắc chắn muốn xóa chương trình học này không? Hành động này không thể hoàn tác.')) {
            return;
        }

        fetch(`/api/chalix/dashboard/program-detail/${programId}/`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            }
        }).then(resp => {
            if (!resp.ok) throw resp;
            alert('Xóa chương trình học thành công');
            if (onSuccess) onSuccess();
        }).catch(err => {
            alert('Lỗi khi xóa chương trình học');
        });
    }

    function deleteCourse(courseId, onSuccess) {
        if (!confirm('Bạn có chắc chắn muốn xóa khóa học này không? Hành động này không thể hoàn tác.')) {
            return;
        }

        fetch(`/api/chalix/dashboard/course-detail/${courseId}/`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            }
        }).then(resp => {
            if (!resp.ok) throw resp;
            alert('Xóa khóa học thành công');
            if (onSuccess) onSuccess();
        }).catch(err => {
            alert('Lỗi khi xóa khóa học');
        });
    }

    // Program creation modal implementation  
    function openCreateProgramModal(onSuccess) {
        console.log('[LM] openCreateProgramModal called');
        // Try to use the improved modal from chalix-cms-interface.js first
        if (window.ChalixCMS && typeof window.ChalixCMS.openCreateProgramModalDirectly === 'function') {
            try {
                console.log('[LM] Using ChalixCMS modal');
                window.ChalixCMS.openCreateProgramModalDirectly();
                // Note: we can't easily pass the callback to the external modal, 
                // so we'll rely on the programs list refresh mechanism
                return;
            } catch (e) {
                console.error('Error calling ChalixCMS.openCreateProgramModalDirectly()', e);
            }
        }
        
        console.log('[LM] Using fallback modal');
        // Fallback: create modal exactly matching Figma design
        const overlay = document.createElement('div');
        overlay.className = 'chalix-modal-overlay';
        
        overlay.innerHTML = `
            <div class="chalix-modal">
                <div class="chalix-modal-header">
                    <span class="chalix-modal-title">TẠO CHƯƠNG TRÌNH HỌC</span>
                    <button class="chalix-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="chalix-modal-content">
                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Tiêu đề chương trình học</label>
                        <input type="text" class="chalix-form-input chalix-input-title" placeholder="Nhập tiêu đề chương trình" />
                    </div>

                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Ký hiệu</label>
                        <div class="chalix-icon-dropdown-wrapper">
                            <button type="button" class="chalix-icon-dropdown-trigger" aria-haspopup="listbox" aria-expanded="false" data-selected="seed-of-life">
                                <div class="chalix-selected-icon"></div>
                                <svg class="chalix-dropdown-arrow" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                                </svg>
                            </button>
                            <div class="chalix-icon-dropdown-menu" style="display: none;" role="listbox">
                                ${getIconOptionsHtml()}
                            </div>
                        </div>
                    </div>

                    <div class="chalix-form-group chalix-switch-group">
                        <label class="chalix-switch-label">
                            <input type="checkbox" name="update_topics" class="chalix-switch-input">
                            <span class="chalix-switch-slider"></span>
                            <span class="chalix-switch-text">Cập nhật các chuyên đề</span>
                        </label>
                    </div>

                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Thêm chuyên đề</label>
                        <div class="chalix-topics-list"></div>
                        <button type="button" class="chalix-add-topic">+ Thêm mới</button>
                    </div>
                </div>

                <div class="chalix-modal-buttons">
                    <button class="chalix-btn-cancel">Hủy</button>
                    <button class="chalix-btn-submit">Tạo chương trình học</button>
                </div>
                <div class="chalix-modal-msg" aria-live="polite"></div>
            </div>
        `;

        // Ensure Figma-accurate styles are injected
        ensureProgramModalStyles();
        
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.chalix-modal-close')?.addEventListener('click', closeModal);
        overlay.querySelector('.chalix-btn-cancel')?.addEventListener('click', closeModal);

        // Setup form functionality similar to the main interface
        setupCreateProgramModal(overlay, onSuccess);
    }

    function getIconOptionsHtml() {
        const icons = ['seed-of-life', 'flower-of-life', 'tree-of-life', 'lotus', 'mandala', 'sacred-geometry'];
        return icons.map(icon => `
            <div class="chalix-icon-option" role="option" tabindex="0" data-icon="${icon}" aria-label="${icon}">
                ${getIconSvg(icon) ? getIconSvg(icon).outerHTML : ''}
            </div>
        `).join('');
    }

    function setupCreateProgramModal(overlay, onSuccess) {
        // Similar to the main interface setup - simplified version
        const submitBtn = overlay.querySelector('.chalix-btn-submit');
        const msgBox = overlay.querySelector('.chalix-modal-msg');

        submitBtn.addEventListener('click', () => {
            const title = overlay.querySelector('.chalix-input-title').value.trim();
            const updateTopics = overlay.querySelector('.chalix-switch-input').checked;
            const selectedIcon = overlay.querySelector('.chalix-icon-dropdown-trigger').dataset.selected || 'seed-of-life';
            const topics = Array.from(overlay.querySelectorAll('.chalix-topic-text')).map(el => el.textContent.trim()).filter(Boolean);

            if (!title) {
                msgBox.textContent = 'Tiêu đề bắt buộc'; 
                msgBox.style.color = '#ef4444'; 
                return;
            }

            msgBox.textContent = 'Đang tạo chương trình học...'; 
            msgBox.style.color = '#6b7280';

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
                body: JSON.stringify({ title: title, icon: selectedIcon, update_topics: updateTopics, topics: topics })
            }).then(resp => { 
                if (!resp.ok) throw resp; 
                return resp.json(); 
            }).then(data => {
                msgBox.style.color = '#10b981'; 
                msgBox.textContent = 'Tạo thành công';
                if (onSuccess) onSuccess();
                setTimeout(() => overlay.remove(), 800);
            }).catch(err => {
                err.text && err.text().then(t => { 
                    let m = 'Lỗi khi tạo chương trình học'; 
                    try { 
                        const ed = JSON.parse(t); 
                        m = ed.error || m; 
                    } catch(e){} 
                    msgBox.textContent = m; 
                    msgBox.style.color = '#ef4444'; 
                }).catch(() => { 
                    msgBox.textContent = 'Lỗi khi tạo chương trình học'; 
                    msgBox.style.color = '#ef4444'; 
                });
            });
        });
    }

    function setupEditProgramModal(overlay, programId) {
        // Similar setup but for editing
        const submitBtn = overlay.querySelector('.chalix-btn-submit');
        const msgBox = overlay.querySelector('.chalix-modal-msg');

        submitBtn.addEventListener('click', () => {
            const title = overlay.querySelector('.chalix-input-title').value.trim();
            const updateTopics = overlay.querySelector('.chalix-switch-input').checked;
            const selectedIcon = overlay.querySelector('.chalix-icon-dropdown-trigger').dataset.selected || 'seed-of-life';
            const topics = Array.from(overlay.querySelectorAll('.chalix-topic-text')).map(el => el.textContent.trim()).filter(Boolean);

            if (!title) {
                msgBox.textContent = 'Tiêu đề bắt buộc'; 
                msgBox.style.color = '#ef4444'; 
                return;
            }

            msgBox.textContent = 'Đang cập nhật chương trình học...'; 
            msgBox.style.color = '#6b7280';

            const url = `/api/chalix/dashboard/program-detail/${programId}/`;
            const csrftoken = getCookie('csrftoken');

            fetch(url, {
                method: 'PUT', 
                credentials: 'same-origin', 
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-CSRFToken': csrftoken, 
                    'Accept': 'application/json' 
                },
                body: JSON.stringify({ title: title, icon: selectedIcon, update_topics: updateTopics, topics: topics })
            }).then(resp => { 
                if (!resp.ok) throw resp; 
                return resp.json(); 
            }).then(data => {
                msgBox.style.color = '#10b981'; 
                msgBox.textContent = 'Cập nhật thành công';
                
                // Refresh the programs list
                const programsContent = document.querySelector('#lm-programs-tab .lm-content-area');
                if (programsContent) {
                    loadProgramsList(programsContent);
                }
                
                setTimeout(() => overlay.remove(), 800);
            }).catch(err => {
                err.text && err.text().then(t => { 
                    let m = 'Lỗi khi cập nhật chương trình học'; 
                    try { 
                        const ed = JSON.parse(t); 
                        m = ed.error || m; 
                    } catch(e){} 
                    msgBox.textContent = m; 
                    msgBox.style.color = '#ef4444'; 
                }).catch(() => { 
                    msgBox.textContent = 'Lỗi khi cập nhật chương trình học'; 
                    msgBox.style.color = '#ef4444'; 
                });
            });
        });
    }
        console.log('[LM] openCreateProgramModal called');
        // Try to use the improved modal from chalix-cms-interface.js first
        if (window.ChalixCMS && typeof window.ChalixCMS.openCreateProgramModalDirectly === 'function') {
            try {
                console.log('[LM] Using ChalixCMS modal');
                window.ChalixCMS.openCreateProgramModalDirectly();
                return;
            } catch (e) {
                console.error('Error calling ChalixCMS.openCreateProgramModalDirectly()', e);
            }
        }
        
        console.log('[LM] Using fallback modal');
        // Fallback: create modal exactly matching Figma design
        const overlay = document.createElement('div');
        overlay.className = 'chalix-modal-overlay';
        
        overlay.innerHTML = `
            <div class="chalix-modal">
                <div class="chalix-modal-header">
                    <span class="chalix-modal-title">TẠO CHƯƠNG TRÌNH HỌC</span>
                    <button class="chalix-modal-close" aria-label="Close">✕</button>
                </div>
                <div class="chalix-modal-content">
                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Tiêu đề chương trình học</label>
                        <input type="text" class="chalix-form-input chalix-input-title" placeholder="Nhập tiêu đề chương trình" />
                    </div>

                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Ký hiệu</label>
                        <div class="chalix-icon-dropdown-wrapper">
                            <button type="button" class="chalix-icon-dropdown-trigger" aria-haspopup="listbox" aria-expanded="false" data-selected="seed-of-life">
                                <div class="chalix-selected-icon"></div>
                                <svg class="chalix-dropdown-arrow" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                                </svg>
                            </button>
                            <div class="chalix-icon-dropdown-menu" style="display: none;" role="listbox">
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="seed-of-life" aria-label="Seed of Life">
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
                                    </svg>
                                </div>
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="flower-of-life" aria-label="Flower of Life">
                                    <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                        <g fill="none" stroke="#111" stroke-width="1">
                                            <circle cx="12" cy="6" r="3" />
                                            <circle cx="16.5" cy="9" r="3" />
                                            <circle cx="12" cy="12" r="3" />
                                            <circle cx="7.5" cy="9" r="3" />
                                            <circle cx="12" cy="18" r="3" />
                                        </g>
                                    </svg>
                                </div>
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="tree-of-life" aria-label="Tree of Life">
                                    <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                        <g fill="none" stroke="#111" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M12 3v4" />
                                            <path d="M7 10c1-2 4-3 5-3s4 1 5 3c.5 1-1 2-2 2s-1-1-3-1-2 1-3 1-2 0-2-1c0-1-2-1.5-1-4z" />
                                            <path d="M6 19c2-1 4-1 6-1s4 0 6 1" />
                                        </g>
                                    </svg>
                                </div>
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="lotus" aria-label="Lotus">
                                    <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                        <g fill="none" stroke="#111" stroke-width="1">
                                            <path d="M12 20s-3-5-7-6c0 0 4-4 7-4s7 4 7 4c-4 1-7 6-7 6z" />
                                            <path d="M4 11s4-3 8-3 8 3 8 3" />
                                        </g>
                                    </svg>
                                </div>
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="mandala" aria-label="Mandala">
                                    <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                        <g fill="none" stroke="#111" stroke-width="1">
                                            <circle cx="12" cy="12" r="2" />
                                            <path d="M12 4v2M12 18v2M4 12h2M18 12h2M6.5 6.5l1.5 1.5M16 16l1.5 1.5M6.5 17.5l1.5-1.5M16 8l1.5-1.5" />
                                        </g>
                                    </svg>
                                </div>
                                <div class="chalix-icon-option" role="option" tabindex="0" data-icon="sacred-geometry" aria-label="Sacred Geometry">
                                    <svg class="chalix-icon-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                                        <g fill="none" stroke="#111" stroke-width="1">
                                            <polygon points="12,3 20,8 20,16 12,21 4,16 4,8" />
                                            <circle cx="12" cy="12" r="2" />
                                        </g>
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="chalix-form-group chalix-switch-group">
                        <label class="chalix-switch-label">
                            <input type="checkbox" name="update_topics" class="chalix-switch-input">
                            <span class="chalix-switch-slider"></span>
                            <span class="chalix-switch-text">Cập nhật các chuyên đề</span>
                        </label>
                    </div>

                    <div class="chalix-form-group">
                        <label class="chalix-form-label">Thêm chuyên đề</label>
                        <div class="chalix-topics-list"></div>
                        <button type="button" class="chalix-add-topic">+ Thêm mới</button>
                    </div>
                </div>

                <div class="chalix-modal-buttons">
                    <button class="chalix-btn-cancel">Hủy</button>
                    <button class="chalix-btn-submit">Tạo chương trình học</button>
                </div>
                <div class="chalix-modal-msg" aria-live="polite"></div>
            </div>
        `;
        // Ensure Figma-accurate styles are injected
        ensureProgramModalStyles();
        
        document.body.appendChild(overlay);

        const closeModal = () => overlay.remove();
        overlay.querySelector('.chalix-modal-close')?.addEventListener('click', closeModal);
        overlay.querySelector('.chalix-btn-cancel')?.addEventListener('click', closeModal);

        // Icon dropdown functionality
        const dropdownTrigger = overlay.querySelector('.chalix-icon-dropdown-trigger');
        const dropdownMenu = overlay.querySelector('.chalix-icon-dropdown-menu');
        const selectedIconContainer = overlay.querySelector('.chalix-selected-icon');
        let isDropdownOpen = false;

        // initialize selected icon in trigger (default to seed-of-life)
        (function initSelected() {
            const current = dropdownTrigger.dataset.selected || 'seed-of-life';
            dropdownTrigger.dataset.selected = current;
            const svgNode = getIconSvg(current);
            if (svgNode) {
                selectedIconContainer.innerHTML = '';
                selectedIconContainer.appendChild(svgNode.cloneNode(true));
                const opt = dropdownMenu.querySelector(`.chalix-icon-option[data-icon="${current}"]`);
                const label = opt && opt.getAttribute ? (opt.getAttribute('aria-label') || current) : current;
                dropdownTrigger.setAttribute('aria-label', label);
            }
            dropdownTrigger.setAttribute('aria-expanded', 'false');
        })();

        // Toggle dropdown
        dropdownTrigger.addEventListener('click', (e) => {
            e.preventDefault();
            isDropdownOpen = !isDropdownOpen;
            dropdownMenu.style.display = isDropdownOpen ? 'block' : 'none';
            dropdownTrigger.classList.toggle('open', isDropdownOpen);
            dropdownTrigger.setAttribute('aria-expanded', isDropdownOpen ? 'true' : 'false');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdownTrigger.contains(e.target) && !dropdownMenu.contains(e.target)) {
                isDropdownOpen = false;
                dropdownMenu.style.display = 'none';
                dropdownTrigger.classList.remove('open');
            }
        });

        // Handle icon selection
        dropdownMenu.querySelectorAll('.chalix-icon-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();

                // Update selected state
                dropdownMenu.querySelectorAll('.chalix-icon-option').forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');

                // Update trigger display
                const iconData = option.dataset.icon;
                const svg = option.querySelector('.chalix-icon-svg');
                const img = option.querySelector('img');
                const label = option.getAttribute('aria-label') || option.dataset.icon || '';

                selectedIconContainer.innerHTML = '';
                if (svg) {
                    selectedIconContainer.appendChild(svg.cloneNode(true));
                } else if (img) {
                    selectedIconContainer.appendChild(img.cloneNode(true));
                } else {
                    // fallback to mapped SVG
                    const mapped = getIconSvg(iconData);
                    if (mapped) selectedIconContainer.appendChild(mapped.cloneNode(true));
                }

                // Update data attribute and ARIA label on trigger (icons-only visible)
                dropdownTrigger.dataset.selected = iconData;
                dropdownTrigger.setAttribute('aria-label', label);

                // Close dropdown
                isDropdownOpen = false;
                dropdownMenu.style.display = 'none';
                dropdownTrigger.classList.remove('open');
            });
        });

        // Topics list and add input behavior (inline input row)
        const addTopicBtn = overlay.querySelector('.chalix-add-topic');
        const topicsList = overlay.querySelector('.chalix-topics-list');
        let isAdding = false;

        addTopicBtn.addEventListener('click', () => {
            if (isAdding) return;
            isAdding = true;
            addTopicBtn.style.display = 'none';

            const inputContainer = document.createElement('div');
            inputContainer.className = 'chalix-topic-input-container';
            inputContainer.innerHTML = `
                <div class="chalix-topic-input-row">
                    <input type="text" class="chalix-topic-input" placeholder="Nhập tên chuyên đề..." maxlength="200" />
                    <div class="chalix-topic-input-actions">
                        <button type="button" class="chalix-topic-save">✓</button>
                        <button type="button" class="chalix-topic-cancel">✕</button>
                    </div>
                </div>
            `;
            topicsList.parentNode.insertBefore(inputContainer, addTopicBtn);

            const input = inputContainer.querySelector('.chalix-topic-input');
            const saveBtn = inputContainer.querySelector('.chalix-topic-save');
            const cancelBtn = inputContainer.querySelector('.chalix-topic-cancel');

            const finishAdd = (save) => {
                const text = input.value.trim();
                if (save && text) {
                    const item = document.createElement('div');
                    item.className = 'chalix-topic-item';
                    item.innerHTML = `
                        <span class="chalix-topic-text">${escapeHtml(text)}</span>
                        <button type="button" class="chalix-topic-remove" data-action="remove">—</button>
                    `;
                    topicsList.appendChild(item);
                }
                inputContainer.remove();
                addTopicBtn.style.display = 'inline-block';
                isAdding = false;
            };

            saveBtn.addEventListener('click', () => finishAdd(true));
            cancelBtn.addEventListener('click', () => finishAdd(false));
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); finishAdd(true); }
                if (e.key === 'Escape') { e.preventDefault(); finishAdd(false); }
            });
            input.focus();
        });

        // Remove topic
        topicsList.addEventListener('click', (e) => {
            if (e.target.classList.contains('chalix-topic-remove')) {
                e.target.closest('.chalix-topic-item').remove();
            }
        });

        // Submit
        const submitBtn = overlay.querySelector('.chalix-btn-submit');
        const msgBox = overlay.querySelector('.chalix-modal-msg');
        submitBtn.addEventListener('click', () => {
            const title = overlay.querySelector('.chalix-input-title').value.trim();
            const updateTopics = overlay.querySelector('.chalix-switch-input').checked;
            const selectedIcon = overlay.querySelector('.chalix-icon-dropdown-trigger').dataset.selected || 'seed-of-life';
            const topics = Array.from(topicsList.querySelectorAll('.chalix-topic-text')).map(el => el.textContent.trim()).filter(Boolean);

            if (!title) {
                msgBox.textContent = 'Tiêu đề bắt buộc'; msgBox.style.color = '#ef4444'; return;
            }
            msgBox.textContent = 'Đang tạo chương trình học...'; msgBox.style.color = '#6b7280';

            const url = '/api/chalix/dashboard/create-program/';
            const csrftoken = (function(){ const v = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)'); return v ? v.pop() : ''; })();

            fetch(url, {
                method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken, 'Accept': 'application/json' },
                body: JSON.stringify({ title: title, icon: selectedIcon, update_topics: updateTopics, topics: topics })
            }).then(resp => { if (!resp.ok) throw resp; return resp.json(); })
            .then(data => {
                msgBox.style.color = '#10b981'; msgBox.textContent = 'Tạo thành công';
                // update placeholder/program list
                const managementContainer = document.getElementById('learning-management-container');
                let placeholder = managementContainer ? managementContainer.querySelector('.lm-placeholder') : null;
                if (!placeholder) placeholder = document.querySelector('.lm-placeholder');
                if (placeholder) {
                    // include the selected icon SVG in the placeholder
                    const iconNode = getIconSvg(data.icon || 'seed-of-life');
                    const iconHtml = iconNode ? iconNode.outerHTML : '';
                    placeholder.innerHTML = `<div style="text-align:left"><strong>${iconHtml} ${escapeHtml(data.title)}</strong> <br/><small>ID: ${data.id} • ${((data.topics && data.topics.length) || 0)} chuyên đề</small></div>`;
                    try { renderProgramList(placeholder); } catch (e) { console.warn('refresh program list failed', e); }
                }
                setTimeout(closeModal, 800);
            }).catch(err => {
                err.text && err.text().then(t => { let m = 'Lỗi khi tạo chương trình học'; try { const ed = JSON.parse(t); m = ed.error || m; } catch(e){} msgBox.textContent = m; msgBox.style.color = '#ef4444'; }).catch(() => { msgBox.textContent = 'Lỗi khi tạo chương trình học'; msgBox.style.color = '#ef4444'; });
            });
        });
    }

    function ensureProgramModalStyles() {
        if (document.getElementById('chalix-program-modal-styles-fallback')) return;
        const css = `
            /* Figma-accurate modal styles for fallback */
            body .chalix-modal-overlay {
                position: fixed !important;
                inset: 0 !important;
                background: rgba(0,0,0,0.45) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 2147483647 !important;
                opacity: 1 !important;
            }

            body .chalix-modal {
                width: 640px !important;
                max-width: 95vw !important;
                background: #ffffff !important;
                border-radius: 20px !important;
                padding: 0 !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.12) !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                transform: scale(1) !important;
                transition: all 200ms ease-out !important;
            }

            body .chalix-modal-header {
                padding: 32px 32px 0 32px !important;
                border-bottom: none !important;
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                margin-bottom: 24px !important;
            }

            body .chalix-modal-title {
                font-size: 24px !important;
                font-weight: 600 !important;
                color: #1a1a1a !important;
                margin: 0 !important;
            }

            body .chalix-modal-close {
                background: none !important;
                border: none !important;
                font-size: 24px !important;
                color: #666666 !important;
                cursor: pointer !important;
                padding: 8px !important;
                border-radius: 50% !important;
                transition: background-color 150ms ease !important;
                width: 40px !important;
                height: 40px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }

            body .chalix-modal-close:hover {
                background: rgba(0,0,0,0.05) !important;
            }

            body .chalix-modal-content {
                padding: 0 32px !important;
                max-height: 60vh !important;
                overflow-y: auto !important;
            }

            body .chalix-form-group {
                margin-bottom: 24px !important;
            }

            body .chalix-form-label {
                display: block !important;
                font-size: 16px !important;
                font-weight: 500 !important;
                color: #374151 !important;
                margin-bottom: 8px !important;
            }

            body .chalix-form-input {
                width: 100% !important;
                padding: 16px !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 12px !important;
                font-size: 16px !important;
                font-family: inherit !important;
                background: #ffffff !important;
                transition: all 150ms ease !important;
                box-sizing: border-box !important;
            }

            body .chalix-form-input:focus {
                outline: none !important;
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
            }

            body .chalix-icon-dropdown-wrapper {
                position: relative !important;
                width: 100% !important;
            }

            body .chalix-icon-dropdown-trigger {
                width: 100% !important;
                padding: 16px !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 12px !important;
                background: #ffffff !important;
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                transition: all 150ms ease !important;
            }

            body .chalix-icon-dropdown-trigger:hover {
                border-color: #9ca3af !important;
            }

            body .chalix-icon-dropdown-trigger:focus {
                outline: none !important;
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
            }

            body .chalix-selected-icon {
                display: flex !important;
                align-items: center !important;
                gap: 12px !important;
            }

            body .chalix-selected-icon img {
                width: 24px !important;
                height: 24px !important;
                object-fit: contain !important;
            }

            /* selected icon SVG sizing */
            body .chalix-selected-icon .chalix-icon-svg {
                width: 24px !important;
                height: 24px !important;
                display: inline-block !important;
            }

            body .chalix-selected-icon span {
                font-size: 16px !important;
                color: #374151 !important;
                font-weight: 500 !important;
            }

            body .chalix-dropdown-arrow {
                width: 20px !important;
                height: 20px !important;
                color: #9ca3af !important;
                transition: transform 150ms ease !important;
            }

            body .chalix-icon-dropdown-trigger.open .chalix-dropdown-arrow {
                transform: rotate(180deg) !important;
            }

            body .chalix-icon-dropdown-menu {
                position: absolute !important;
                top: 100% !important;
                left: 0 !important;
                right: 0 !important;
                background: #ffffff !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 12px !important;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06) !important;
                z-index: 1000 !important;
                margin-top: 4px !important;
                max-height: 240px !important;
                overflow-y: auto !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option {
                width: auto !important;
                height: auto !important;
                border: none !important;
                border-radius: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: flex-start !important;
                cursor: pointer !important;
                transition: all 150ms ease !important;
                background: #ffffff !important;
                padding: 12px 16px !important;
                gap: 12px !important;
                border-bottom: 1px solid #f3f4f6 !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option:last-child {
                border-bottom: none !important;
                border-radius: 0 0 10px 10px !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option:first-child {
                border-radius: 10px 10px 0 0 !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option:only-child {
                border-radius: 10px !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option:hover {
                background: #f8fafc !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option.selected {
                background: #eff6ff !important;
                color: #3b82f6 !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option img,
            body .chalix-icon-dropdown-menu .chalix-icon-option .chalix-icon-svg {
                width: 24px !important;
                height: 24px !important;
                display: inline-block !important;
            }

            body .chalix-icon-dropdown-menu .chalix-icon-option span {
                font-size: 16px !important;
                color: inherit !important;
                font-weight: 500 !important;
            }

            body .chalix-switch-group {
                padding: 16px 0 !important;
            }

            body .chalix-switch-label {
                display: flex !important;
                align-items: center !important;
                gap: 12px !important;
                cursor: pointer !important;
            }

            body .chalix-switch-input {
                display: none !important;
            }

            body .chalix-switch-slider {
                width: 48px !important;
                height: 28px !important;
                background: #d1d5db !important;
                border-radius: 14px !important;
                position: relative !important;
                transition: all 200ms ease !important;
                flex-shrink: 0 !important;
            }

            body .chalix-switch-slider::before {
                content: '' !important;
                position: absolute !important;
                top: 2px !important;
                left: 2px !important;
                width: 24px !important;
                height: 24px !important;
                background: #ffffff !important;
                border-radius: 50% !important;
                transition: all 200ms ease !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            }

            body .chalix-switch-input:checked + .chalix-switch-slider {
                background: #3b82f6 !important;
            }

            body .chalix-switch-input:checked + .chalix-switch-slider::before {
                transform: translateX(20px) !important;
            }

            body .chalix-switch-text {
                font-size: 16px !important;
                color: #374151 !important;
                font-weight: 500 !important;
            }

            body .chalix-topics-list {
                margin-bottom: 16px !important;
            }

            body .chalix-topic-item {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                background: #f8fafc !important;
                padding: 16px !important;
                margin-bottom: 8px !important;
                border-radius: 12px !important;
                border: 1px solid #e2e8f0 !important;
            }

            body .chalix-topic-text {
                flex: 1 !important;
                font-size: 16px !important;
                color: #374151 !important;
            }

            body .chalix-topic-remove {
                background: #ef4444 !important;
                color: #ffffff !important;
                border: none !important;
                width: 32px !important;
                height: 32px !important;
                border-radius: 50% !important;
                cursor: pointer !important;
                font-size: 16px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: background-color 150ms ease !important;
            }

            body .chalix-topic-remove:hover {
                background: #dc2626 !important;
            }

            body .chalix-add-topic {
                background: #10b981 !important;
                color: #ffffff !important;
                border: none !important;
                padding: 12px 20px !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 14px !important;
                cursor: pointer !important;
                transition: background-color 150ms ease !important;
            }

            body .chalix-add-topic:hover {
                background: #059669 !important;
            }

            body .chalix-modal-buttons {
                padding: 24px 32px 32px 32px !important;
                display: flex !important;
                gap: 16px !important;
                justify-content: flex-end !important;
            }

            body .chalix-btn-cancel {
                padding: 12px 24px !important;
                border: 2px solid #d1d5db !important;
                background: #ffffff !important;
                color: #6b7280 !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 16px !important;
                cursor: pointer !important;
                transition: all 150ms ease !important;
            }

            body .chalix-btn-cancel:hover {
                background: #f9fafb !important;
                border-color: #9ca3af !important;
            }

            body .chalix-btn-submit {
                padding: 12px 24px !important;
                border: none !important;
                background: #3b82f6 !important;
                color: #ffffff !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 16px !important;
                cursor: pointer !important;
                transition: background-color 150ms ease !important;
            }

            body .chalix-btn-submit:hover {
                background: #2563eb !important;
            }

            body .chalix-btn-submit:disabled {
                background: #9ca3af !important;
                cursor: not-allowed !important;
            }

            body .chalix-modal-msg {
                margin: 16px 0 0 0 !important;
                font-size: 14px !important;
                font-weight: 500 !important;
            }

            /* Topic input styles */
            body .chalix-topic-input-container {
                margin-bottom: 12px !important;
            }

            body .chalix-topic-input-row {
                display: flex !important;
                gap: 8px !important;
                align-items: center !important;
            }

            body .chalix-topic-input {
                flex: 1 !important;
                padding: 12px 16px !important;
                border: 2px solid #e5e7eb !important;
                border-radius: 8px !important;
                font-size: 16px !important;
                font-family: inherit !important;
            }

            body .chalix-topic-input:focus {
                outline: none !important;
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
            }

            body .chalix-topic-input-actions {
                display: flex !important;
                gap: 4px !important;
            }

            body .chalix-topic-save, body .chalix-topic-cancel {
                width: 32px !important;
                height: 32px !important;
                border: none !important;
                border-radius: 50% !important;
                cursor: pointer !important;
                font-size: 16px !important;
                font-weight: bold !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 150ms ease !important;
            }

            body .chalix-topic-save {
                background: #10b981 !important;
                color: #ffffff !important;
            }

            body .chalix-topic-save:hover {
                background: #059669 !important;
            }

            body .chalix-topic-cancel {
                background: #ef4444 !important;
                color: #ffffff !important;
            }

            body .chalix-topic-cancel:hover {
                background: #dc2626 !important;
            }
        `;
        const s = document.createElement('style'); 
        s.id = 'chalix-program-modal-styles-fallback'; 
        s.appendChild(document.createTextNode(css)); 
        document.head.appendChild(s);
    }

    function ensureModalStyles() {
        if (document.getElementById('lm-modal-styles')) return;
        const css = `
            .lm-modal-overlay{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(3,11,19,0.5);z-index:1200}
            .lm-modal{background:#fff;border-radius:10px;max-width:720px;width:94%;padding:18px;box-shadow:0 10px 30px rgba(7,22,34,0.25)}
            .lm-modal-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
            .lm-modal-header h3{margin:0}
            .lm-modal-close{background:transparent;border:0;font-size:18px;cursor:pointer}
            .lm-modal-body label{display:block;margin:8px 0;color:#3b4750}
            .lm-modal-body select{width:100%;padding:10px;border:1px solid #d7dee3;border-radius:6px;font-size:15px;background:#fff}
            .lm-modal-body input.lm-input-title, .lm-modal-body textarea.lm-input-desc{width:100%;padding:10px;border:1px solid #d7dee3;border-radius:6px;font-size:15px;box-sizing:border-box}
            .lm-modal-body textarea.lm-input-desc{min-height:140px}
            .lm-modal-body select, .lm-modal-body input, .lm-modal-body textarea{box-sizing:border-box}
            .lm-modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:12px}
            .lm-modal-msg{margin-top:8px;font-size:14px}
        `;
        const s = document.createElement('style'); s.id = 'lm-modal-styles'; s.appendChild(document.createTextNode(css)); document.head.appendChild(s);
    }

    // small util to read cookie
    function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function escapeHtml(str){ return String(str).replace(/[&<>"'`]/g, function(s){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;","`":"&#x60;"}[s]; }); }


    // Fetch and render the course list inside the provided placeholder
    function renderCourseList(placeholder) {
        if (!placeholder) return;
        const listContainerId = 'lm-course-list';
        let listContainer = placeholder.querySelector('#' + listContainerId);
        if (!listContainer) {
            listContainer = document.createElement('div');
            listContainer.id = listContainerId;
            listContainer.style.textAlign = 'left';
            listContainer.innerHTML = '<div style="color:#546470">Đang tải danh sách khóa học...</div>';
            placeholder.innerHTML = '<h3 style="margin:0 0 8px;">Danh sách khóa học</h3>';
            placeholder.appendChild(listContainer);
        }

        fetch('/api/chalix/dashboard/list-courses/', { credentials: 'same-origin', headers: { 'Accept': 'application/json' }})
            .then(resp => { if (!resp.ok) throw resp; return resp.json(); })
            .then(data => {
                const courses = data.courses || [];
                if (courses.length === 0) {
                    listContainer.innerHTML = '<div style="color:#546470">Chưa có khóa học nào.</div>';
                    return;
                }
                const html = ['<ul style="list-style:none;padding:0;margin:0">'];
                for (const c of courses) {
                    html.push(`<li style="padding:10px 0;border-bottom:1px solid #eef6fa"><strong>${escapeHtml(c.title)}</strong><div style="color:#6b7680;font-size:13px">${escapeHtml(c.short_description || '')}</div><div style="color:#94a3ad;font-size:12px;margin-top:6px">ID: ${c.id} • Tạo bởi: ${escapeHtml(c.created_by || '—')} • ${new Date(c.created_at).toLocaleString()}</div></li>`);
                }
                html.push('</ul>');
                listContainer.innerHTML = html.join('');
            }).catch(() => {
                listContainer.innerHTML = '<div style="color:#c23">Lỗi khi tải danh sách khóa học.</div>';
            });
    }

    // Fetch and render the program list inside the provided placeholder
    function renderProgramList(placeholder) {
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
                    const topicsList = p.topics.map(t => escapeHtml(t.title)).join(', ');
                    const iconNode = getIconSvg(p.icon || 'seed-of-life');
                    const iconHtml = iconNode ? iconNode.outerHTML : escapeHtml(p.icon || '');
                    html.push(`<li style="padding:10px 0;border-bottom:1px solid #eef6fa">
                        <strong>${iconHtml} ${escapeHtml(p.title)}</strong>
                        <div style="color:#6b7680;font-size:13px;margin:4px 0">${escapeHtml(p.icon)} • ${p.update_topics ? 'Tự động cập nhật' : 'Cố định'}</div>
                        <div style="color:#6b7680;font-size:13px;margin:4px 0"><strong>Chuyên đề:</strong> ${topicsList || 'Không có'}</div>
                        <div style="color:#94a3ad;font-size:12px;margin-top:6px">ID: ${p.id} • ${p.topics.length} chuyên đề • Tạo bởi: ${escapeHtml(p.created_by || '—')} • ${new Date(p.created_at).toLocaleString()}</div>
                    </li>`);
                }
                html.push('</ul>');
                listContainer.innerHTML = html.join('');
            }).catch(() => {
                listContainer.innerHTML = '<div style="color:#c23">Lỗi khi tải danh sách chương trình học.</div>';
            });
    }

    window.CMS_TABS['learning-management'] = {
        render: render,
        openCreateProgramModal: openCreateProgramModal,
        openCreateCourseModal: openCreateCourseModal
    };

})();
