/*
 * Management Tab Renderer - Organizations Only
 * Handles organization management (create, edit, delete, view)
 */
(function () {
    'use strict';

    window.CMS_TABS = window.CMS_TABS || {};

    function ensureStyles() {
        if (document.getElementById('cms-management-styles')) return;
        const css = `
            .mgmt-wrap { display: flex; width: 100%; padding: 32px 24px; box-sizing: border-box; }
            .mgmt-card { width: 100%; max-width: none; background: transparent; padding: 0; }
            
            .mgmt-tab-header { 
                display: flex; justify-content: space-between; align-items: center; 
                margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;
            }
            .mgmt-tab-header h3 { margin: 0; font-size: 24px; font-weight: 700; color: #1f2937; }
            
            .mgmt-btn { 
                display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; 
                border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; 
                transition: all 200ms ease; text-decoration: none;
            }
            .mgmt-btn.primary { background: #3b82f6; color: #fff; }
            .mgmt-btn.primary:hover { background: #2563eb; }
            
            .mgmt-loading { text-align: center; padding: 40px; color: #6b7280; }
            .mgmt-error { text-align: center; padding: 40px; color: #ef4444; }
            .mgmt-empty { text-align: center; padding: 40px; color: #9ca3af; }
        `;
        const style = document.createElement('style');
        style.id = 'cms-management-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    function render(container, config) {
        if (!container) return;
        console.log('[Management] Starting render for management tab (organizations only)');
        ensureStyles();

        container.innerHTML = `
            <div class="mgmt-wrap">
                <div class="mgmt-card">
                    <!-- Organizations Management -->
                    <div id="mgmt-organizations-view">
                        <div class="mgmt-tab-header">
                            <h3>Cơ quan</h3>
                            <button class="mgmt-btn primary" data-action="create-organization" id="create-org-btn">
                                <span class="mgmt-btn-icon">+</span>
                                Tạo cơ quan
                            </button>
                        </div>
                        <div class="mgmt-content-area" id="organizations-content-area">
                            <div class="mgmt-loading">Đang tải danh sách cơ quan...</div>
                        </div>
                    </div>
                    
                    <!-- Professional Fields Management -->
                    <div id="mgmt-professional-fields-view" style="margin-top: 48px;">
                        <div class="mgmt-tab-header">
                            <h3>Lĩnh vực chuyên môn</h3>
                            <button class="mgmt-btn primary" data-action="create-professional-field" id="create-field-btn">
                                <span class="mgmt-btn-icon">+</span>
                                Tạo lĩnh vực
                            </button>
                        </div>
                        <div class="mgmt-content-area" id="professional-fields-content-area">
                            <div class="mgmt-loading">Đang tải danh sách lĩnh vực chuyên môn...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Initialize action buttons
        initializeActionButtons(container);
        
        // Load organizations list
        loadOrganizationsList(container.querySelector('#organizations-content-area'));
        
        // Load professional fields list
        loadProfessionalFieldsList(container.querySelector('#professional-fields-content-area'));
        
        console.log('[Management] Management tab render completed successfully');
    }

    function initializeActionButtons(container) {
        container.querySelectorAll('.mgmt-btn[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.dataset.action;
                
                if (action === 'create-organization') {
                    const contentArea = container.querySelector('#organizations-content-area');
                    showCreateModal(contentArea);
                } else if (action === 'create-professional-field') {
                    const contentArea = container.querySelector('#professional-fields-content-area');
                    showCreateFieldModal(contentArea);
                }
            });
        });
    }

    function loadOrganizationsList(contentArea) {
        if (!contentArea) return;
        
        contentArea.innerHTML = '<div class="mgmt-loading">Đang tải danh sách cơ quan...</div>';

        fetch('/api/v1/organizations/', {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const organizations = data.results || data.organizations || [];
            renderOrganizationsList(contentArea, organizations);
        })
        .catch(err => {
            console.error('Failed to load organizations:', err);
            contentArea.innerHTML = '<div class="mgmt-error">Không thể tải danh sách cơ quan. Vui lòng thử lại.</div>';
        });
    }

    function renderOrganizationsList(contentArea, organizations) {
        if (!contentArea) return;

        if (organizations.length === 0) {
            contentArea.innerHTML = '<div class="mgmt-empty">Chưa có cơ quan nào.</div>';
            return;
        }

        // Create table
        const tableHtml = `
            <div style="background: #fff; border: 1px solid #e6eef6; border-radius: 12px; padding: 18px; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; font-size: 14px;">
                    <thead>
                        <tr>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">ID</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Tên cơ quan</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Ngày tạo</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Ngày cập nhật</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Quản trị viên</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: center; white-space: nowrap;">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${organizations.map(org => `
                            <tr style="border-bottom: 1px solid #eef6fb;">
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${org.id}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${escapeHtml(org.name)}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${formatDate(org.created_at)}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${formatDate(org.updated_at)}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${org.admin_username || '—'}</td>
                                <td style="padding: 18px 16px; vertical-align: middle; text-align: center;">
                                    <button class="mgmt-action-btn edit" data-id="${org.id}" style="background: transparent; border: 1px solid #00aaed; color: #00aaed; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 6px;">Sửa</button>
                                    <button class="mgmt-action-btn delete" data-id="${org.id}" style="background: transparent; border: 1px solid #dc3545; color: #dc3545; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">Xóa</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        contentArea.innerHTML = tableHtml;

        // Add event listeners for action buttons
        contentArea.querySelectorAll('.mgmt-action-btn.edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const orgId = btn.dataset.id;
                editOrganization(orgId, contentArea);
            });
        });

        contentArea.querySelectorAll('.mgmt-action-btn.delete').forEach(btn => {
            btn.addEventListener('click', () => {
                const orgId = btn.dataset.id;
                deleteOrganization(orgId, contentArea);
            });
        });
    }

    function showNotification(overlay, type, message) {
        const notification = overlay.querySelector('#modal-notification');
        const icon = notification.querySelector('.mgmt-notification-icon');
        const messageEl = notification.querySelector('.mgmt-notification-message');
        
        notification.className = 'mgmt-notification show ' + type;
        icon.textContent = type === 'success' ? '✓' : '✕';
        messageEl.textContent = message;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }

    function showCreateModal(contentArea) {
        // Fetch available users first
        fetch('/api/v1/organizations/staff-users/', {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const users = data.users || [];
            renderCreateModal(contentArea, users);
        })
        .catch(err => {
            console.error('Failed to load users:', err);
            alert('Không thể tải danh sách người dùng. Vui lòng thử lại.');
        });
    }

    function renderCreateModal(contentArea, allUsers) {
        ensureModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'mgmt-modal-overlay';
        
        overlay.innerHTML = `
            <div class="mgmt-modal">
                <div class="mgmt-modal-header">
                    <h3 class="mgmt-modal-title">Tạo cơ quan mới</h3>
                    <button class="mgmt-modal-close" aria-label="Đóng">×</button>
                </div>
                <div class="mgmt-modal-body">
                    <div class="mgmt-notification" id="modal-notification">
                        <span class="mgmt-notification-icon"></span>
                        <span class="mgmt-notification-message"></span>
                    </div>
                    <form id="createOrgForm">
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên cơ quan *</label>
                            <input type="text" name="name" required class="mgmt-form-input" placeholder="Ví dụ: Sở Giáo dục TP.HCM">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên hiển thị</label>
                            <input type="text" name="display_name" class="mgmt-form-input" placeholder="Display name (optional)">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mã cơ quan *</label>
                            <input type="text" name="code" required class="mgmt-form-input" placeholder="Ví dụ: HCMC_DOE">
                            <div class="mgmt-form-help">Mã định danh duy nhất cho cơ quan</div>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mô tả</label>
                            <textarea name="description" class="mgmt-form-input mgmt-form-textarea" placeholder="Mô tả về cơ quan (tùy chọn)"></textarea>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Admin cơ quan</label>
                            <div id="selected-admin-container"></div>
                            <div class="mgmt-user-search">
                                <input 
                                    type="text" 
                                    id="admin-search-input" 
                                    class="mgmt-user-search-input" 
                                    placeholder="Tìm theo username hoặc email..."
                                    autocomplete="off"
                                >
                                <div id="admin-dropdown" class="mgmt-user-dropdown"></div>
                            </div>
                            <input type="hidden" name="admin" id="admin-id" value="">
                            <div class="mgmt-form-help">Tìm kiếm và chọn người dùng để làm admin cơ quan</div>
                        </div>
                    </form>
                    <div class="mgmt-modal-actions">
                        <button class="mgmt-btn secondary mgmt-cancel-btn">Hủy</button>
                        <button class="mgmt-btn primary mgmt-create-btn">Tạo cơ quan</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Setup user search functionality
        let selectedAdminId = null;
        const searchInput = overlay.querySelector('#admin-search-input');
        const dropdown = overlay.querySelector('#admin-dropdown');
        const adminIdInput = overlay.querySelector('#admin-id');
        const selectedContainer = overlay.querySelector('#selected-admin-container');
        
        function showSelectedAdmin(user) {
            selectedContainer.innerHTML = `
                <div class="mgmt-user-selected">
                    <div class="mgmt-user-selected-info">
                        <div class="mgmt-user-selected-name">${user.full_name}</div>
                        <div class="mgmt-user-selected-email">${user.username} (${user.email})</div>
                    </div>
                    <button type="button" class="mgmt-user-remove" title="Xóa admin">×</button>
                </div>
            `;
            
            selectedContainer.querySelector('.mgmt-user-remove').addEventListener('click', () => {
                selectedAdminId = null;
                adminIdInput.value = '';
                selectedContainer.innerHTML = '';
                searchInput.style.display = 'block';
                searchInput.value = '';
                searchInput.focus();
            });
        }
        
        function filterUsers(query) {
            if (!query) return allUsers;
            const lowerQuery = query.toLowerCase();
            return allUsers.filter(user => 
                user.username.toLowerCase().includes(lowerQuery) ||
                user.email.toLowerCase().includes(lowerQuery) ||
                user.full_name.toLowerCase().includes(lowerQuery)
            );
        }
        
        function renderDropdown(users) {
            if (users.length === 0) {
                dropdown.innerHTML = '<div style="padding: 8px 12px; color: #6b7280;">Không tìm thấy người dùng</div>';
                dropdown.classList.add('show');
                return;
            }
            
            dropdown.innerHTML = users.slice(0, 10).map(user => `
                <div class="mgmt-user-option" data-user-id="${user.id}">
                    <div class="mgmt-user-option-name">${user.full_name}</div>
                    <div class="mgmt-user-option-email">${user.username} (${user.email})</div>
                </div>
            `).join('');
            dropdown.classList.add('show');
            
            // Add click handlers
            dropdown.querySelectorAll('.mgmt-user-option').forEach(option => {
                option.addEventListener('click', () => {
                    const userId = parseInt(option.dataset.userId);
                    const user = allUsers.find(u => u.id === userId);
                    if (user) {
                        selectedAdminId = userId;
                        adminIdInput.value = userId;
                        showSelectedAdmin(user);
                        searchInput.style.display = 'none';
                        searchInput.value = '';
                        dropdown.classList.remove('show');
                    }
                });
            });
        }
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value;
            const filtered = filterUsers(query);
            renderDropdown(filtered);
        });
        
        searchInput.addEventListener('focus', () => {
            if (searchInput.value) {
                const filtered = filterUsers(searchInput.value);
                renderDropdown(filtered);
            } else {
                renderDropdown(allUsers);
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
        
        // Close modal handlers
        const closeModal = () => {
            document.body.removeChild(overlay);
        };
        
        overlay.querySelector('.mgmt-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.mgmt-cancel-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
        
        // Create handler
        const form = overlay.querySelector('#createOrgForm');
        overlay.querySelector('.mgmt-create-btn').addEventListener('click', () => {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            const data = {
                name: form.querySelector('[name="name"]').value,
                display_name: form.querySelector('[name="display_name"]').value || '',
                code: form.querySelector('[name="code"]').value,
                description: form.querySelector('[name="description"]').value || '',
                is_active: true,
                admin: adminIdInput.value ? parseInt(adminIdInput.value) : null
            };
            
            const createBtn = overlay.querySelector('.mgmt-create-btn');
            createBtn.disabled = true;
            createBtn.textContent = 'Đang tạo...';
            
            fetch('/api/v1/organizations/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(resp => {
                if (!resp.ok) {
                    return resp.json().then(err => { throw err; });
                }
                return resp.json();
            })
            .then(() => {
                showNotification(overlay, 'success', 'Tạo cơ quan thành công!');
                form.reset();
                selectedContainer.innerHTML = '';
                adminIdInput.value = '';
                searchInput.style.display = 'block';
                
                // Close modal after 1.5 seconds and reload list
                setTimeout(() => {
                    closeModal();
                    loadOrganizationsList(contentArea);
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to create organization:', err);
                const errorMsg = err.error || err.message || 'Không thể tạo cơ quan. Vui lòng thử lại.';
                showNotification(overlay, 'error', errorMsg);
            })
            .finally(() => {
                createBtn.disabled = false;
                createBtn.textContent = 'Tạo cơ quan';
            });
        });
    }

    function editOrganization(orgId, contentArea) {
        // Fetch organization details
        fetch(`/api/v1/organizations/${orgId}/`, {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(org => {
            showEditModal(org, contentArea);
        })
        .catch(err => {
            console.error('Failed to load organization:', err);
            alert('Không thể tải thông tin cơ quan. Vui lòng thử lại.');
        });
    }

    function ensureModalStyles() {
        if (document.getElementById('mgmt-modal-styles')) return;
        
        const css = `
            .mgmt-modal-overlay *,
            .mgmt-modal-overlay *::before,
            .mgmt-modal-overlay *::after {
                box-sizing: border-box;
            }
            
            .mgmt-modal-overlay {
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
            
            .mgmt-modal {
                background: white;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 90vh;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
                box-sizing: border-box;
            }
            
            .mgmt-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
                flex-shrink: 0;
            }
            
            .mgmt-modal-title {
                font-size: 18px;
                font-weight: 600;
                margin: 0;
                color: #1f2937;
            }
            
            .mgmt-modal-close {
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
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            
            .mgmt-modal-close:hover {
                background-color: #f3f4f6;
                color: #1f2937;
            }
            
            .mgmt-modal-body {
                padding: 24px;
                overflow-y: auto;
                flex: 1;
            }
            
            .mgmt-notification {
                padding: 12px 16px;
                border-radius: 6px;
                margin-bottom: 16px;
                display: none;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                animation: slideDown 0.3s ease;
            }
            
            .mgmt-notification.show {
                display: flex;
            }
            
            .mgmt-notification.success {
                background: #d1fae5;
                color: #065f46;
                border: 1px solid #6ee7b7;
            }
            
            .mgmt-notification.error {
                background: #fee2e2;
                color: #991b1b;
                border: 1px solid #fca5a5;
            }
            
            .mgmt-notification-icon {
                font-size: 18px;
                font-weight: bold;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .mgmt-form-group {
                margin-bottom: 16px;
            }
            
            .mgmt-form-label {
                display: block;
                margin-bottom: 6px;
                font-weight: 500;
                font-size: 14px;
                color: #374151;
            }
            
            .mgmt-form-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #b2b2b2;
                border-radius: 4px;
                font-size: 14px;
                transition: border-color 0.2s;
                box-sizing: border-box;
            }
            
            .mgmt-form-input:focus {
                outline: none;
                border-color: #00aaed;
            }
            
            .mgmt-form-input:read-only {
                background: #f6f7f8;
                cursor: not-allowed;
            }
            
            .mgmt-form-textarea {
                min-height: 100px;
                resize: vertical;
                box-sizing: border-box;
            }
            
            .mgmt-form-help {
                margin-top: 4px;
                font-size: 12px;
                color: #6b7280;
            }
            
            .mgmt-user-search {
                position: relative;
            }
            
            .mgmt-user-search-input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #b2b2b2;
                border-radius: 4px;
                font-size: 14px;
                box-sizing: border-box;
            }
            
            .mgmt-user-search-input:focus {
                outline: none;
                border-color: #00aaed;
            }
            
            .mgmt-user-dropdown {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                max-height: 200px;
                overflow-y: auto;
                background: white;
                border: 1px solid #b2b2b2;
                border-top: none;
                border-radius: 0 0 4px 4px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 10;
                display: none;
            }
            
            .mgmt-user-dropdown.show {
                display: block;
            }
            
            .mgmt-user-option {
                padding: 8px 12px;
                cursor: pointer;
                transition: background-color 0.15s;
            }
            
            .mgmt-user-option:hover {
                background-color: #f3f4f6;
            }
            
            .mgmt-user-option.selected {
                background-color: #e3f2fd;
            }
            
            .mgmt-user-option-name {
                font-weight: 500;
                color: #1f2937;
            }
            
            .mgmt-user-option-email {
                font-size: 12px;
                color: #6b7280;
            }
            
            .mgmt-user-selected {
                padding: 8px 12px;
                background: #e3f2fd;
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .mgmt-user-selected-info {
                flex: 1;
            }
            
            .mgmt-user-selected-name {
                font-weight: 500;
                color: #1f2937;
            }
            
            .mgmt-user-selected-email {
                font-size: 12px;
                color: #6b7280;
            }
            
            .mgmt-user-remove {
                background: transparent;
                border: none;
                color: #ef4444;
                cursor: pointer;
                font-size: 18px;
                padding: 0 4px;
            }
            
            .mgmt-user-remove:hover {
                color: #dc2626;
            }
            
            .mgmt-modal-actions {
                display: flex;
                justify-content: flex-end;
                gap: 12px;
                margin-top: 24px;
                padding-top: 16px;
                border-top: 1px solid #e5e7eb;
            }
            
            .mgmt-btn {
                padding: 10px 24px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                border: none;
                transition: all 0.2s;
            }
            
            .mgmt-btn.primary {
                background: #00aaed;
                color: white;
            }
            
            .mgmt-btn.primary:hover {
                background: #0090cc;
            }
            
            .mgmt-btn.secondary {
                background: transparent;
                border: 1px solid #b2b2b2;
                color: #333;
            }
            
            .mgmt-btn.secondary:hover {
                background: #f6f7f8;
            }
        `;
        
        const style = document.createElement('style');
        style.id = 'mgmt-modal-styles';
        style.textContent = css;
        document.head.appendChild(style);
    }

    function showEditModal(org, contentArea) {
        ensureModalStyles();
        
        // Fetch available users first
        fetch('/api/v1/organizations/staff-users/', {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const users = data.users || [];
            renderEditModal(org, contentArea, users);
        })
        .catch(err => {
            console.error('Failed to load users:', err);
            // Still render modal but with empty users list
            renderEditModal(org, contentArea, []);
        });
    }

    function renderEditModal(org, contentArea, allUsers) {
        const overlay = document.createElement('div');
        overlay.className = 'mgmt-modal-overlay';
        
        // Find current admin user info
        const currentAdmin = org.admin ? allUsers.find(u => u.id === org.admin) : null;
        
        overlay.innerHTML = `
            <div class="mgmt-modal">
                <div class="mgmt-modal-header">
                    <h3 class="mgmt-modal-title">Chỉnh sửa cơ quan</h3>
                    <button class="mgmt-modal-close" aria-label="Đóng">×</button>
                </div>
                <div class="mgmt-modal-body">
                    <div class="mgmt-notification" id="modal-notification">
                        <span class="mgmt-notification-icon"></span>
                        <span class="mgmt-notification-message"></span>
                    </div>
                    <form id="editOrgForm">
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên cơ quan *</label>
                            <input type="text" name="name" value="${escapeHtml(org.name || '')}" required class="mgmt-form-input">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mã cơ quan</label>
                            <input type="text" name="code" value="${escapeHtml(org.code || '')}" readonly class="mgmt-form-input">
                            <div class="mgmt-form-help">Mã định danh không thể thay đổi</div>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên hiển thị</label>
                            <input type="text" name="display_name" value="${escapeHtml(org.display_name || '')}" class="mgmt-form-input">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mô tả</label>
                            <textarea name="description" class="mgmt-form-input mgmt-form-textarea">${escapeHtml(org.description || '')}</textarea>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Admin cơ quan</label>
                            <div id="selected-admin-container"></div>
                            <div class="mgmt-user-search">
                                <input 
                                    type="text" 
                                    id="admin-search-input" 
                                    class="mgmt-user-search-input" 
                                    placeholder="Tìm theo username hoặc email..."
                                    autocomplete="off"
                                >
                                <div id="admin-dropdown" class="mgmt-user-dropdown"></div>
                            </div>
                            <input type="hidden" name="admin" id="admin-id" value="${org.admin || ''}">
                            <div class="mgmt-form-help">Tìm kiếm và chọn người dùng để làm admin cơ quan</div>
                        </div>
                    </form>
                    <div class="mgmt-modal-actions">
                        <button class="mgmt-btn secondary mgmt-cancel-btn">Hủy</button>
                        <button class="mgmt-btn primary mgmt-save-btn">Lưu thay đổi</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Setup user search functionality
        let selectedAdminId = org.admin;
        const searchInput = overlay.querySelector('#admin-search-input');
        const dropdown = overlay.querySelector('#admin-dropdown');
        const adminIdInput = overlay.querySelector('#admin-id');
        const selectedContainer = overlay.querySelector('#selected-admin-container');
        
        // Show current admin if exists
        if (currentAdmin) {
            showSelectedAdmin(currentAdmin);
            searchInput.style.display = 'none';
        }
        
        function showSelectedAdmin(user) {
            selectedContainer.innerHTML = `
                <div class="mgmt-user-selected">
                    <div class="mgmt-user-selected-info">
                        <div class="mgmt-user-selected-name">${user.full_name}</div>
                        <div class="mgmt-user-selected-email">${user.username} (${user.email})</div>
                    </div>
                    <button type="button" class="mgmt-user-remove" title="Xóa admin">×</button>
                </div>
            `;
            
            selectedContainer.querySelector('.mgmt-user-remove').addEventListener('click', () => {
                selectedAdminId = null;
                adminIdInput.value = '';
                selectedContainer.innerHTML = '';
                searchInput.style.display = 'block';
                searchInput.value = '';
                searchInput.focus();
            });
        }
        
        function filterUsers(query) {
            if (!query) return allUsers;
            const lowerQuery = query.toLowerCase();
            return allUsers.filter(user => 
                user.username.toLowerCase().includes(lowerQuery) ||
                user.email.toLowerCase().includes(lowerQuery) ||
                user.full_name.toLowerCase().includes(lowerQuery)
            );
        }
        
        function renderDropdown(users) {
            if (users.length === 0) {
                dropdown.innerHTML = '<div style="padding: 8px 12px; color: #6b7280;">Không tìm thấy người dùng</div>';
                dropdown.classList.add('show');
                return;
            }
            
            dropdown.innerHTML = users.slice(0, 10).map(user => `
                <div class="mgmt-user-option" data-user-id="${user.id}">
                    <div class="mgmt-user-option-name">${user.full_name}</div>
                    <div class="mgmt-user-option-email">${user.username} (${user.email})</div>
                </div>
            `).join('');
            dropdown.classList.add('show');
            
            // Add click handlers
            dropdown.querySelectorAll('.mgmt-user-option').forEach(option => {
                option.addEventListener('click', () => {
                    const userId = parseInt(option.dataset.userId);
                    const user = allUsers.find(u => u.id === userId);
                    if (user) {
                        selectedAdminId = userId;
                        adminIdInput.value = userId;
                        showSelectedAdmin(user);
                        searchInput.style.display = 'none';
                        searchInput.value = '';
                        dropdown.classList.remove('show');
                    }
                });
            });
        }
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value;
            const filtered = filterUsers(query);
            renderDropdown(filtered);
        });
        
        searchInput.addEventListener('focus', () => {
            if (searchInput.value) {
                const filtered = filterUsers(searchInput.value);
                renderDropdown(filtered);
            } else {
                renderDropdown(allUsers);
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
        
        // Close modal handlers
        const closeModal = () => {
            document.body.removeChild(overlay);
        };
        
        overlay.querySelector('.mgmt-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.mgmt-cancel-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
        
        // Save handler
        const form = overlay.querySelector('#editOrgForm');
        overlay.querySelector('.mgmt-save-btn').addEventListener('click', () => {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            const data = {
                name: form.querySelector('[name="name"]').value,
                display_name: form.querySelector('[name="display_name"]').value || '',
                description: form.querySelector('[name="description"]').value || '',
                admin: adminIdInput.value ? parseInt(adminIdInput.value) : null
            };
            
            const saveBtn = overlay.querySelector('.mgmt-save-btn');
            saveBtn.disabled = true;
            saveBtn.textContent = 'Đang lưu...';
            
            fetch(`/api/v1/organizations/${org.id}/`, {
                method: 'PATCH',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(resp => {
                if (!resp.ok) {
                    return resp.json().then(err => { throw err; });
                }
                return resp.json();
            })
            .then(() => {
                showNotification(overlay, 'success', 'Cập nhật cơ quan thành công!');
                
                // Close modal after 1.5 seconds and reload list
                setTimeout(() => {
                    closeModal();
                    loadOrganizationsList(contentArea);
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to update organization:', err);
                const errorMsg = err.error || err.message || 'Không thể cập nhật cơ quan. Vui lòng thử lại.';
                showNotification(overlay, 'error', errorMsg);
            })
            .finally(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Lưu thay đổi';
            });
        });
    }

    function deleteOrganization(orgId, contentArea) {
        if (confirm('Bạn có chắc chắn muốn xóa cơ quan này?')) {
            fetch(`/api/v1/organizations/${orgId}/`, {
                method: 'DELETE',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                loadOrganizationsList(contentArea);
            })
            .catch(err => {
                console.error('Failed to delete organization:', err);
                alert('Không thể xóa cơ quan. Vui lòng thử lại.');
            });
        }
    }

    function formatDate(dateString) {
        if (!dateString) return '—';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('vi-VN');
        } catch (e) {
            return '—';
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

    // ============================================================================
    // Professional Fields Management Functions
    // ============================================================================

    function loadProfessionalFieldsList(contentArea) {
        if (!contentArea) return;
        
        contentArea.innerHTML = '<div class="mgmt-loading">Đang tải danh sách lĩnh vực chuyên môn...</div>';

        fetch('/api/v1/professional_fields/', {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(data => {
            const fields = Array.isArray(data) ? data : (data.results || []);
            renderProfessionalFieldsList(contentArea, fields);
        })
        .catch(err => {
            console.error('Failed to load professional fields:', err);
            contentArea.innerHTML = '<div class="mgmt-error">Không thể tải danh sách lĩnh vực chuyên môn. Vui lòng thử lại.</div>';
        });
    }

    function renderProfessionalFieldsList(contentArea, fields) {
        if (!contentArea) return;

        if (fields.length === 0) {
            contentArea.innerHTML = '<div class="mgmt-empty">Chưa có lĩnh vực chuyên môn nào.</div>';
            return;
        }

        // Create table
        const tableHtml = `
            <div style="background: #fff; border: 1px solid #e6eef6; border-radius: 12px; padding: 18px; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; font-size: 14px;">
                    <thead>
                        <tr>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">ID</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Tên lĩnh vực</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Thứ tự</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: center; white-space: nowrap;">Trạng thái</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: left; white-space: nowrap;">Ngày tạo</th>
                            <th style="padding: 18px 16px; font-weight:600; color:#374151; text-align: center; white-space: nowrap;">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${fields.map(field => `
                            <tr style="border-bottom: 1px solid #eef6fb;">
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${field.id}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${escapeHtml(field.name)}</td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${field.sort_order || 0}</td>
                                <td style="padding: 18px 16px; vertical-align: middle; text-align: center;">
                                    <span style="padding: 4px 8px; border-radius: 4px; font-size: 12px; background: ${field.is_active ? '#d1fae5' : '#fee2e2'}; color: ${field.is_active ? '#065f46' : '#991b1b'};">${field.is_active ? 'Hoạt động' : 'Vô hiệu'}</span>
                                </td>
                                <td style="padding: 18px 16px; color:#374151; vertical-align: middle; text-align: left;">${formatDate(field.created)}</td>
                                <td style="padding: 18px 16px; vertical-align: middle; text-align: center;">
                                    <button class="mgmt-action-btn edit-field" data-id="${field.id}" style="background: transparent; border: 1px solid #00aaed; color: #00aaed; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-right: 6px;">Sửa</button>
                                    <button class="mgmt-action-btn delete-field" data-id="${field.id}" style="background: transparent; border: 1px solid #dc3545; color: #dc3545; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">Xóa</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        contentArea.innerHTML = tableHtml;

        // Add event listeners for action buttons
        contentArea.querySelectorAll('.mgmt-action-btn.edit-field').forEach(btn => {
            btn.addEventListener('click', () => {
                const fieldId = btn.dataset.id;
                editProfessionalField(fieldId, contentArea);
            });
        });

        contentArea.querySelectorAll('.mgmt-action-btn.delete-field').forEach(btn => {
            btn.addEventListener('click', () => {
                const fieldId = btn.dataset.id;
                deleteProfessionalField(fieldId, contentArea);
            });
        });
    }

    function showCreateFieldModal(contentArea) {
        renderCreateFieldModal(contentArea);
    }

    function renderCreateFieldModal(contentArea) {
        ensureModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'mgmt-modal-overlay';
        
        overlay.innerHTML = `
            <div class="mgmt-modal">
                <div class="mgmt-modal-header">
                    <h3 class="mgmt-modal-title">Tạo lĩnh vực chuyên môn mới</h3>
                    <button class="mgmt-modal-close" aria-label="Đóng">×</button>
                </div>
                <div class="mgmt-modal-body">
                    <div class="mgmt-notification" id="modal-notification">
                        <span class="mgmt-notification-icon"></span>
                        <span class="mgmt-notification-message"></span>
                    </div>
                    <form id="createFieldForm">
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên lĩnh vực *</label>
                            <input type="text" name="name" required class="mgmt-form-input" placeholder="Ví dụ: Toán học">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mô tả</label>
                            <textarea name="description" class="mgmt-form-input mgmt-form-textarea" placeholder="Mô tả về lĩnh vực chuyên môn (tùy chọn)"></textarea>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Thứ tự sắp xếp</label>
                            <input type="number" name="sort_order" value="0" min="0" class="mgmt-form-input" placeholder="0">
                            <div class="mgmt-form-help">Số thấp hơn sẽ hiển thị trước</div>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" name="is_active" checked style="width: auto;">
                                <span class="mgmt-form-label" style="margin: 0;">Kích hoạt</span>
                            </label>
                        </div>
                    </form>
                    <div class="mgmt-modal-actions">
                        <button class="mgmt-btn secondary mgmt-cancel-btn">Hủy</button>
                        <button class="mgmt-btn primary mgmt-create-field-btn">Tạo lĩnh vực</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Close modal handlers
        const closeModal = () => {
            document.body.removeChild(overlay);
        };
        
        overlay.querySelector('.mgmt-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.mgmt-cancel-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
        
        // Create handler
        const form = overlay.querySelector('#createFieldForm');
        overlay.querySelector('.mgmt-create-field-btn').addEventListener('click', () => {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            const data = {
                name: form.querySelector('[name="name"]').value,
                description: form.querySelector('[name="description"]').value || '',
                sort_order: parseInt(form.querySelector('[name="sort_order"]').value) || 0,
                is_active: form.querySelector('[name="is_active"]').checked
            };
            
            const createBtn = overlay.querySelector('.mgmt-create-field-btn');
            createBtn.disabled = true;
            createBtn.textContent = 'Đang tạo...';
            
            fetch('/api/v1/professional_fields/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(resp => {
                if (!resp.ok) {
                    return resp.json().then(err => { throw err; });
                }
                return resp.json();
            })
            .then(() => {
                showNotification(overlay, 'success', 'Tạo lĩnh vực chuyên môn thành công!');
                form.reset();
                
                // Close modal after 1.5 seconds and reload list
                setTimeout(() => {
                    closeModal();
                    loadProfessionalFieldsList(contentArea);
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to create professional field:', err);
                const errorMsg = err.error || err.message || 'Không thể tạo lĩnh vực chuyên môn. Vui lòng thử lại.';
                showNotification(overlay, 'error', errorMsg);
            })
            .finally(() => {
                createBtn.disabled = false;
                createBtn.textContent = 'Tạo lĩnh vực';
            });
        });
    }

    function editProfessionalField(fieldId, contentArea) {
        // Fetch field details
        fetch(`/api/v1/professional_fields/${fieldId}/`, {
            credentials: 'same-origin',
            headers: { 
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(resp => {
            if (!resp.ok) throw resp;
            return resp.json();
        })
        .then(field => {
            showEditFieldModal(field, contentArea);
        })
        .catch(err => {
            console.error('Failed to load professional field:', err);
            alert('Không thể tải thông tin lĩnh vực chuyên môn. Vui lòng thử lại.');
        });
    }

    function showEditFieldModal(field, contentArea) {
        renderEditFieldModal(field, contentArea);
    }

    function renderEditFieldModal(field, contentArea) {
        ensureModalStyles();
        
        const overlay = document.createElement('div');
        overlay.className = 'mgmt-modal-overlay';
        
        overlay.innerHTML = `
            <div class="mgmt-modal">
                <div class="mgmt-modal-header">
                    <h3 class="mgmt-modal-title">Chỉnh sửa lĩnh vực chuyên môn</h3>
                    <button class="mgmt-modal-close" aria-label="Đóng">×</button>
                </div>
                <div class="mgmt-modal-body">
                    <div class="mgmt-notification" id="modal-notification">
                        <span class="mgmt-notification-icon"></span>
                        <span class="mgmt-notification-message"></span>
                    </div>
                    <form id="editFieldForm">
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Tên lĩnh vực *</label>
                            <input type="text" name="name" value="${escapeHtml(field.name || '')}" required class="mgmt-form-input">
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Mô tả</label>
                            <textarea name="description" class="mgmt-form-input mgmt-form-textarea">${escapeHtml(field.description || '')}</textarea>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label class="mgmt-form-label">Thứ tự sắp xếp</label>
                            <input type="number" name="sort_order" value="${field.sort_order || 0}" min="0" class="mgmt-form-input">
                            <div class="mgmt-form-help">Số thấp hơn sẽ hiển thị trước</div>
                        </div>
                        
                        <div class="mgmt-form-group">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" name="is_active" ${field.is_active ? 'checked' : ''} style="width: auto;">
                                <span class="mgmt-form-label" style="margin: 0;">Kích hoạt</span>
                            </label>
                        </div>
                    </form>
                    <div class="mgmt-modal-actions">
                        <button class="mgmt-btn secondary mgmt-cancel-btn">Hủy</button>
                        <button class="mgmt-btn primary mgmt-save-field-btn">Lưu thay đổi</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Close modal handlers
        const closeModal = () => {
            document.body.removeChild(overlay);
        };
        
        overlay.querySelector('.mgmt-modal-close').addEventListener('click', closeModal);
        overlay.querySelector('.mgmt-cancel-btn').addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
        
        // Save handler
        const form = overlay.querySelector('#editFieldForm');
        overlay.querySelector('.mgmt-save-field-btn').addEventListener('click', () => {
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            const data = {
                name: form.querySelector('[name="name"]').value,
                description: form.querySelector('[name="description"]').value || '',
                sort_order: parseInt(form.querySelector('[name="sort_order"]').value) || 0,
                is_active: form.querySelector('[name="is_active"]').checked
            };
            
            const saveBtn = overlay.querySelector('.mgmt-save-field-btn');
            saveBtn.disabled = true;
            saveBtn.textContent = 'Đang lưu...';
            
            fetch(`/api/v1/professional_fields/${field.id}/`, {
                method: 'PATCH',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            })
            .then(resp => {
                if (!resp.ok) {
                    return resp.json().then(err => { throw err; });
                }
                return resp.json();
            })
            .then(() => {
                showNotification(overlay, 'success', 'Cập nhật lĩnh vực chuyên môn thành công!');
                
                // Close modal after 1.5 seconds and reload list
                setTimeout(() => {
                    closeModal();
                    loadProfessionalFieldsList(contentArea);
                }, 1500);
            })
            .catch(err => {
                console.error('Failed to update professional field:', err);
                const errorMsg = err.error || err.message || 'Không thể cập nhật lĩnh vực chuyên môn. Vui lòng thử lại.';
                showNotification(overlay, 'error', errorMsg);
            })
            .finally(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Lưu thay đổi';
            });
        });
    }

    function deleteProfessionalField(fieldId, contentArea) {
        if (confirm('Bạn có chắc chắn muốn xóa lĩnh vực chuyên môn này?')) {
            fetch(`/api/v1/professional_fields/${fieldId}/`, {
                method: 'DELETE',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(resp => {
                if (!resp.ok) throw resp;
                loadProfessionalFieldsList(contentArea);
            })
            .catch(err => {
                console.error('Failed to delete professional field:', err);
                alert('Không thể xóa lĩnh vực chuyên môn. Vui lòng thử lại.');
            });
        }
    }

    // Register the module
    window.CMS_TABS['management'] = {
        render: render
    };

})();
