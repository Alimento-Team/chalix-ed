/*
 * Create Account Tab Renderer
 * Exposes a renderer via window.CMS_TABS['create-account'].render(container, config)
 */
(function () {
    'use strict';

    window.CMS_TABS = window.CMS_TABS || {};

    function ensureStyles() {
        if (document.getElementById('cms-create-account-styles')) return;
        const css = `
            .create-account-wrap { display:flex; justify-content:center; padding:32px 12px; }
            .create-account-card { max-width:980px; width:100%; background: #fff; padding:28px; border-radius:6px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.04); }
            .create-account-title { font-size:20px; margin:0 0 6px; font-weight:600; }
            .create-account-desc { color:#536070; margin:0 0 18px; }
            .create-account-cta { display:flex; gap:16px; justify-content:flex-start; align-items:center; flex-wrap:wrap; margin: 18px 0 12px; }
            .cta-btn { min-width:220px; padding:14px 20px; border-radius:6px; font-size:16px; font-weight:600; cursor:pointer; border: none; }
            .cta-primary { background: #00aaed; color: #fff; box-shadow: 0 1px 0 rgba(0,0,0,0.06); }
            .cta-secondary { background: #3494c8; color:#fff; }
            .create-account-placeholder { margin-top:18px; padding:16px; border-radius:6px; background:#fbfdff; border:1px solid #e6f2fb; color:#274a5a; }
            .single-account-form input, .single-account-form select { font-size:14px; line-height:1.5; }
            .single-account-form input:focus, .single-account-form select:focus { outline:none; border-color:#00aaed; box-shadow:0 0 0 2px rgba(0,170,237,0.2); }
            .single-account-form select option { font-size:14px; line-height:1.5; padding:8px 12px; min-height:24px; }
            .single-account-form select { background-size: 16px 16px; }
            @media (max-width:768px){ 
                .cta-btn{ width:100%; min-width:0; } 
                .create-account-cta{flex-direction:column;} 
                .single-account-form > div[style*="grid-template-columns"] { grid-template-columns: 1fr !important; }
            }
        `;
        const style = document.createElement('style');
        style.id = 'cms-create-account-styles';
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    function render(container, config) {
        if (!container) return;
        ensureStyles();

        container.innerHTML = `
            <div class="create-account-wrap">
                <div class="create-account-card">
                    <!-- Excel Upload Button - Top Right -->
                    <div style="position: relative;">
                        <div style="position: absolute; top: -10px; right: 0; display: flex; gap: 12px; align-items: center;">
                            <button type="button" class="excel-upload-btn" id="excel-upload-btn" style="background: #3494c8; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 500; display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif;">
                                <i class="fa fa-upload"></i>
                                Nhập danh sách người dùng bằng file excel
                            </button>
                            <button type="button" class="download-template-btn" id="download-template-btn" style="background: #6c757d; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 8px; font-family: 'Inter', sans-serif;">
                                <i class="fa fa-download"></i>
                                Tải file mẫu
                            </button>
                            <input type="file" id="excel-file-input" accept=".xlsx,.xls,.csv" style="display: none;">
                        </div>
                    </div>
                    
                    <h2 class="create-account-title" style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 18px; color: #1e1e1e; margin: 60px 0 30px 0;">NHẬP THÔNG TIN THÊM MỚI NGƯỜI DÙNG</h2>
                    
                    <form class="chalix-form" id="user-creation-form" style="max-width: none;">
                        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Họ và tên</label>
                                <input type="text" name="full_name" placeholder="Tên người dùng sẽ được hiển thị trên tất cả các trang" required 
                                       style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box;" />
                            </div>
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Email hoặc Số điện thoại</label>
                                <input type="email" name="email" placeholder="Nhập email hoặc số điện thoại" required 
                                       style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box;" />
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Nhập mật khẩu</label>
                                <input type="password" name="password" placeholder="Nhập mật khẩu" required 
                                       style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box;" />
                            </div>
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Vai trò người dùng</label>
                                <select name="role" required style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box; appearance: none; background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" viewBox=\"0 0 16 16\"><path fill=\"%23666\" d=\"M8 12L3 6h10l-5 6z\"/></svg>'); background-repeat: no-repeat; background-position: right 12px center;">
                                    <option value="">Chọn vai trò người dùng</option>
                                </select>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 20px; margin-bottom: 40px;">
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Lựa chọn quyền</label>
                                <select name="permissions" required style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box; appearance: none; background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" viewBox=\"0 0 16 16\"><path fill=\"%23666\" d=\"M8 12L3 6h10l-5 6z\"/></svg>'); background-repeat: no-repeat; background-position: right 12px center;">
                                    <option value="system_admin" selected>Quản trị hệ thống</option>
                                    <option value="content_manager">Quản lý nội dung</option>
                                    <option value="instructor">Giảng viên</option>
                                    <option value="learner">Học viên</option>
                                </select>
                            </div>
                            <div style="flex: 1; max-width: 580px;">
                                <label style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 16px; color: #1e1e1e; line-height: 1.4; display: block; margin-bottom: 8px;">Trạng thái</label>
                                <select name="status" required style="width: 100%; min-width: 240px; height: 48px; padding: 12px 16px; border: 1px solid #d9d9d9; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.5; color: #1e1e1e; background: #fff; box-sizing: border-box; appearance: none; background-image: url('data:image/svg+xml;charset=US-ASCII,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" viewBox=\"0 0 16 16\"><path fill=\"%23666\" d=\"M8 12L3 6h10l-5 6z\"/></svg>'); background-repeat: no-repeat; background-position: right 12px center;">
                                    <option value="active" selected>Hoạt động</option>
                                    <option value="inactive">Không hoạt động</option>
                                </select>
                            </div>
                        </div>
                        
                        <div style="display: flex; justify-content: flex-end; padding-top: 20px;">
                            <button type="submit" style="background: #00aaed; color: #f5f5f5; border: none; border-radius: 8px; padding: 12px 24px; font-family: 'Inter', sans-serif; font-weight: 500; font-size: 16px; cursor: pointer; min-width: 150px;">
                                Tạo mới
                            </button>
                        </div>
                    </form>
                    
                    <!-- Success/Error Messages -->
                    <div id="user-creation-messages" style="display: none; margin-top: 20px;">
                        <div class="message success" id="success-message" style="display: none; padding: 12px; border-radius: 8px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb;"></div>
                        <div class="message error" id="error-message" style="display: none; padding: 12px; border-radius: 8px; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"></div>
                    </div>
                </div>
            </div>
        `;

        const wrap = container;
        
        // Handle form submission
        const form = wrap.querySelector('#user-creation-form');
        const excelUploadBtn = wrap.querySelector('#excel-upload-btn');
        const downloadTemplateBtn = wrap.querySelector('#download-template-btn');
        const excelFileInput = wrap.querySelector('#excel-file-input');
        const messagesContainer = wrap.querySelector('#user-creation-messages');
        const successMessage = wrap.querySelector('#success-message');
        const errorMessage = wrap.querySelector('#error-message');
        
        // Form submission handler
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                // Clear previous messages
                hideMessages();
                
                // Get form data
                const formData = new FormData(form);
                const userData = Object.fromEntries(formData.entries());
                
                // Validate required fields
                if (!validateUserData(userData)) {
                    return;
                }
                
                // Set loading state
                setLoadingState(true);
                
                try {
                    const response = await fetch('/api/contentstore/v1/users/create', {
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
            });
        }
        
        // Excel upload button handler
        if (excelUploadBtn) {
            excelUploadBtn.addEventListener('click', () => {
                if (excelFileInput) {
                    excelFileInput.click();
                }
            });
        }
        
        // Download template button handler
        if (downloadTemplateBtn) {
            downloadTemplateBtn.addEventListener('click', handleTemplateDownload);
        }
        
        // File input change handler
        if (excelFileInput) {
            excelFileInput.addEventListener('change', handleFileUpload);
        }
        
        // Load initial data (roles)
        loadInitialData();
        
        // Helper functions
        function validateUserData(userData) {
            const requiredFields = {
                'full_name': 'Họ và tên',
                'email': 'Email',
                'password': 'Mật khẩu',
                'role': 'Vai trò',
                'status': 'Trạng thái'
            };
            
            let isValid = true;
            
            Object.entries(requiredFields).forEach(([field, label]) => {
                if (!userData[field] || userData[field].trim() === '') {
                    showError(`${label} là bắt buộc`);
                    isValid = false;
                }
            });
            
            // Validate email format
            if (userData.email) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(userData.email)) {
                    showError('Email không hợp lệ');
                    isValid = false;
                }
            }
            
            // Validate password strength
            if (userData.password && userData.password.length < 6) {
                showError('Mật khẩu phải có ít nhất 6 ký tự');
                isValid = false;
            }
            
            return isValid;
        }
        
        function setLoadingState(loading) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (!submitBtn) return;
            
            if (loading) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Đang tạo...';
            } else {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Tạo mới';
            }
        }
        
        function showSuccess(message) {
            if (successMessage && messagesContainer) {
                successMessage.textContent = message;
                successMessage.style.display = 'block';
                errorMessage.style.display = 'none';
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
                    successMessage.style.display = 'none';
                }
                if (errorMessage) {
                    errorMessage.style.display = 'none';
                }
            }
        }
        
        function showUserCreatedInfo(user) {
            console.log('User created:', user);
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
        
        async function loadInitialData() {
            try {
                const response = await fetch('/api/contentstore/v1/users/roles', {
                    credentials: 'include',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        populateRoleDropdown(data.roles);
                    }
                }
            } catch (error) {
                console.error('Error loading initial data:', error);
            }
        }
        
        function populateRoleDropdown(roles) {
            const roleSelect = form.querySelector('select[name="role"]');
            if (!roleSelect) return;
            
            // Clear existing options except placeholder
            while (roleSelect.children.length > 1) {
                roleSelect.removeChild(roleSelect.lastChild);
            }
            
            // Add available roles
            roles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.value;
                option.textContent = role.display_name;
                roleSelect.appendChild(option);
            });
        }
        
        function handleTemplateDownload() {
            // Create download link
            const downloadUrl = '/api/contentstore/v1/users/template/download';
            
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
        
        function handleFileUpload(event) {
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
            
            // Show upload modal or handle upload directly
            uploadUsersFile(file);
        }
        
        async function uploadUsersFile(file) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/contentstore/v1/users/bulk-create', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken()
                    },
                    credentials: 'include',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showSuccess(`Tạo thành công ${result.created_count} tài khoản`);
                } else {
                    showError(result.message || 'Lỗi tải file');
                }
                
            } catch (error) {
                console.error('Error uploading file:', error);
                showError('Lỗi tải file. Vui lòng thử lại.');
            }
        }
        
        // Event handlers setup complete
    }

    window.CMS_TABS['create-account'] = {
        render: render
    };

})();
