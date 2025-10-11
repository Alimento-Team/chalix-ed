/**
 * Chalix CMS User Creation Interface
 * Vietnamese interface for creating user accounts with role management
 */

(function() {
    'use strict';

    // Configuration
    const API_BASE = '/api/contentstore/v1';
    const ENDPOINTS = {
        CREATE_USER: `${API_BASE}/users/create`,
        BULK_CREATE: `${API_BASE}/users/bulk-create`,
        ORGANIZATIONS: `${API_BASE}/users/organizations`,
        ROLES: `${API_BASE}/users/roles`
    };

    // State management
    let currentUserRole = null;
    let availableRoles = [];
    let availableOrganizations = [];

    // DOM Elements
    let form = null;
    let excelUploadBtn = null;
    let excelFileInput = null;
    let messagesContainer = null;
    let successMessage = null;
    let errorMessage = null;

    // Initialize when DOM is ready
    function init() {
        // Check if we're on the user creation tab
        const userCreationPanel = document.getElementById('user-creation-panel');
        if (!userCreationPanel) {
            return;
        }

        // Get DOM elements
        form = document.getElementById('user-creation-form');
        excelUploadBtn = document.getElementById('excel-upload-btn');
        excelFileInput = document.getElementById('excel-file-input');
        messagesContainer = document.getElementById('user-creation-messages');
        successMessage = document.getElementById('success-message');
        errorMessage = document.getElementById('error-message');

        if (!form) {
            console.error('User creation form not found');
            return;
        }

        // Load initial data
        loadInitialData();

        // Set up event listeners
        setupEventListeners();
    }

    async function loadInitialData() {
        try {
            // Load available roles and organizations in parallel
            const [rolesResponse, orgsResponse] = await Promise.all([
                fetch(ENDPOINTS.ROLES, {
                    credentials: 'include',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                }),
                fetch(ENDPOINTS.ORGANIZATIONS, {
                    credentials: 'include',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                })
            ]);

            if (rolesResponse.ok) {
                const rolesData = await rolesResponse.json();
                if (rolesData.success) {
                    availableRoles = rolesData.roles;
                    populateRoleDropdown();
                }
            }

            if (orgsResponse.ok) {
                const orgsData = await orgsResponse.json();
                if (orgsData.success) {
                    availableOrganizations = orgsData.organizations;
                    // Organizations will be used when needed for specific roles
                }
            }

        } catch (error) {
            console.error('Error loading initial data:', error);
            showError('Lỗi tải dữ liệu ban đầu. Vui lòng tải lại trang.');
        }
    }

    function populateRoleDropdown() {
        const roleSelect = document.getElementById('user-role');
        if (!roleSelect) return;

        // Clear existing options except placeholder
        while (roleSelect.children.length > 1) {
            roleSelect.removeChild(roleSelect.lastChild);
        }

        // Add available roles
        availableRoles.forEach(role => {
            const option = document.createElement('option');
            option.value = role.value;
            option.textContent = role.display_name;
            roleSelect.appendChild(option);
        });
    }

    function setupEventListeners() {
        // Form submission
        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }

        // Excel upload button
        if (excelUploadBtn) {
            excelUploadBtn.addEventListener('click', () => {
                if (excelFileInput) {
                    excelFileInput.click();
                }
            });
        }

        // Download template button
        const downloadTemplateBtn = document.getElementById('download-template-btn');
        if (downloadTemplateBtn) {
            downloadTemplateBtn.addEventListener('click', handleTemplateDownload);
        }

        // File input change
        if (excelFileInput) {
            excelFileInput.addEventListener('change', handleFileUpload);
        }

        // Role change to show organization field if needed
        const roleSelect = document.getElementById('user-role');
        if (roleSelect) {
            roleSelect.addEventListener('change', handleRoleChange);
        }
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        
        if (form.classList.contains('loading')) {
            return;
        }

        // Clear previous messages
        hideMessages();

        // Validate form
        const formData = new FormData(form);
        const userData = Object.fromEntries(formData.entries());

        if (!validateUserData(userData)) {
            return;
        }

        // Set loading state
        setLoadingState(true);

        try {
            const response = await fetch(ENDPOINTS.CREATE_USER, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'include',
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (result.success) {
                showSuccess(result.message);
                form.reset();
                
                // Show created user info
                if (result.user) {
                    showUserCreatedInfo(result.user);
                }
            } else {
                showError(result.message || 'Lỗi tạo tài khoản');
            }

        } catch (error) {
            console.error('Error creating user:', error);
            showError('Lỗi kết nối. Vui lòng thử lại.');
        } finally {
            setLoadingState(false);
        }
    }

    function validateUserData(userData) {
        // Clear previous field errors
        clearFieldErrors();

        let isValid = true;

        // Check required fields
        const requiredFields = {
            'full_name': 'Họ và tên',
            'email': 'Email',
            'password': 'Mật khẩu', 
            'role': 'Vai trò',
            'status': 'Trạng thái'
        };

        Object.entries(requiredFields).forEach(([field, label]) => {
            if (!userData[field] || userData[field].trim() === '') {
                showFieldError(field, `${label} là bắt buộc`);
                isValid = false;
            }
        });

        // Validate email format
        if (userData.email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(userData.email)) {
                showFieldError('email', 'Email không hợp lệ');
                isValid = false;
            }
        }

        // Validate password strength
        if (userData.password && userData.password.length < 6) {
            showFieldError('password', 'Mật khẩu phải có ít nhất 6 ký tự');
            isValid = false;
        }

        return isValid;
    }

    function showFieldError(fieldName, message) {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (!field) return;

        const formField = field.closest('.form-field');
        if (formField) {
            formField.classList.add('error');
            
            // Remove existing error message
            const existingError = formField.querySelector('.field-error');
            if (existingError) {
                existingError.remove();
            }

            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.textContent = message;
            formField.appendChild(errorDiv);
        }
    }

    function clearFieldErrors() {
        document.querySelectorAll('.form-field.error').forEach(field => {
            field.classList.remove('error');
        });
        document.querySelectorAll('.field-error').forEach(error => {
            error.remove();
        });
    }

    async function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['.xlsx', '.xls', '.csv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            showError('File phải có định dạng Excel (.xlsx, .xls) hoặc CSV');
            event.target.value = '';
            return;
        }

        // Show upload modal
        showUploadModal(file);
    }

    function showUploadModal(file) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'upload-modal';
        modal.innerHTML = `
            <div class="upload-modal-content">
                <h3>Tải lên danh sách người dùng</h3>
                <p>Đang xử lý file: <strong>${file.name}</strong></p>
                <div class="upload-progress">
                    <div class="progress-bar">
                        <div class="progress-bar-fill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">Đang tải lên...</div>
                </div>
                <div class="upload-results" style="display: none;">
                    <!-- Results will be populated here -->
                </div>
                <div class="modal-actions">
                    <button type="button" class="modal-btn secondary" id="close-modal">Đóng</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Set up modal events
        const closeBtn = modal.querySelector('#close-modal');
        closeBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
            excelFileInput.value = ''; // Reset file input
        });

        // Start upload
        uploadUsersFile(file, modal);
    }

    async function uploadUsersFile(file, modal) {
        const progressBar = modal.querySelector('.progress-bar-fill');
        const progressText = modal.querySelector('.progress-text');
        const resultsContainer = modal.querySelector('.upload-results');

        try {
            // Update progress
            progressBar.style.width = '30%';
            progressText.textContent = 'Đang xử lý file...';

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(ENDPOINTS.BULK_CREATE, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'include',
                body: formData
            });

            // Update progress
            progressBar.style.width = '70%';
            progressText.textContent = 'Đang tạo tài khoản...';

            const result = await response.json();

            // Complete progress
            progressBar.style.width = '100%';
            progressText.textContent = 'Hoàn thành!';

            // Show results
            showUploadResults(result, resultsContainer);

        } catch (error) {
            console.error('Error uploading file:', error);
            progressText.textContent = 'Lỗi tải file!';
            progressText.style.color = '#dc3545';
            
            resultsContainer.innerHTML = `
                <div class="error-list">
                    <p>Lỗi: ${error.message || 'Không thể tải file'}</p>
                </div>
            `;
            resultsContainer.style.display = 'block';
        }
    }

    function showUploadResults(result, container) {
        let html = '';

        if (result.success) {
            html += `<h4>✅ Tạo thành công ${result.created_count} tài khoản</h4>`;
            
            if (result.created_users && result.created_users.length > 0) {
                html += '<div class="user-list">';
                result.created_users.forEach(user => {
                    html += `
                        <div class="user-item">
                            <strong>${user.full_name}</strong> - ${user.email} 
                            <br><small>Vai trò: ${user.role} | Mật khẩu: ${user.password}</small>
                        </div>
                    `;
                });
                html += '</div>';
            }

            if (result.errors && result.errors.length > 0) {
                html += `<h4>⚠️ ${result.error_count} lỗi</h4>`;
                html += '<div class="error-list">';
                result.errors.forEach(error => {
                    html += `<div>${error}</div>`;
                });
                html += '</div>';
            }
        } else {
            html += `<h4>❌ Lỗi tạo tài khoản</h4>`;
            html += `<div class="error-list">${result.message}`;
            
            if (result.errors && result.errors.length > 0) {
                result.errors.forEach(error => {
                    html += `<div>${error}</div>`;
                });
            }
            html += '</div>';
        }

        container.innerHTML = html;
        container.style.display = 'block';
    }

    function handleRoleChange(event) {
        const selectedRole = event.target.value;
        
        // For some roles, we might need to show organization selection
        // This can be implemented based on business requirements
        console.log('Role selected:', selectedRole);
    }

    function showUserCreatedInfo(user) {
        // You can implement a more detailed user info display here
        const message = `
            Tài khoản đã được tạo thành công:
            - Họ tên: ${user.full_name}
            - Email: ${user.email}
            - Vai trò: ${user.role}
            - Trạng thái: ${user.is_active ? 'Hoạt động' : 'Không hoạt động'}
        `;
        
        console.log('User created:', user);
    }

    function setLoadingState(loading) {
        if (!form) return;

        if (loading) {
            form.classList.add('loading');
            const submitBtn = form.querySelector('.btn-create');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add('loading');
                submitBtn.textContent = 'Đang tạo...';
            }
        } else {
            form.classList.remove('loading');
            const submitBtn = form.querySelector('.btn-create');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
                submitBtn.textContent = 'Tạo mới';
            }
        }
    }

    function showSuccess(message) {
        if (successMessage && messagesContainer) {
            successMessage.textContent = message;
            successMessage.classList.add('show');
            errorMessage.style.display = 'none';
            successMessage.style.display = 'block';
            messagesContainer.style.display = 'block';
            
            // Auto hide after 5 seconds
            setTimeout(() => {
                hideMessages();
            }, 5000);
        }
    }

    function showError(message) {
        if (errorMessage && messagesContainer) {
            errorMessage.textContent = message;
            successMessage.style.display = 'none';
            errorMessage.style.display = 'block';
            messagesContainer.style.display = 'block';
        }
    }

    function hideMessages() {
        if (messagesContainer) {
            messagesContainer.style.display = 'none';
            if (successMessage) {
                successMessage.classList.remove('show');
            }
        }
    }

    function getCSRFToken() {
        // Get CSRF token from cookie or meta tag
        const token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     getCookie('csrftoken');
        return token;
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

    function handleTemplateDownload() {
        // Create download link
        const downloadUrl = `${API_BASE}/users/template/download`;
        
        // Create a temporary anchor element to trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = 'chalix_user_template.csv';
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success message
        showSuccess('File mẫu đã được tải xuống. Vui lòng kiểm tra thư mục Downloads của bạn.');
    }

    // Export for potential external use
    window.ChalixUserCreation = {
        init: init,
        loadInitialData: loadInitialData
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();