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
            .single-account-form input, .single-account-form select { font-size:14px; }
            .single-account-form input:focus, .single-account-form select:focus { outline:none; border-color:#00aaed; box-shadow:0 0 0 2px rgba(0,170,237,0.2); }
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
                    <h2 class="create-account-title">${config.contentTitle}</h2>
                    <p class="create-account-desc">${config.contentDescription}</p>

                    <div class="create-account-cta">
                        <button class="cta-btn cta-primary" data-action="single">Tạo tài khoản đơn lẻ</button>
                        <button class="cta-btn cta-secondary" data-action="bulk">Tạo nhiều tài khoản</button>
                    </div>

                    <div class="create-account-placeholder">
                        <p>Chọn hành động để bắt đầu: tạo tài khoản đơn lẻ hoặc tạo nhiều tài khoản cùng lúc.</p>
                    </div>
                </div>
            </div>
        `;

        const wrap = container;
        wrap.querySelectorAll('.cta-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const placeholder = wrap.querySelector('.create-account-placeholder');
                if (action === 'single') {
                    placeholder.innerHTML = `
                        <h3 style="margin:0 0 8px;">Tạo tài khoản đơn lẻ</h3>
                        <p style="margin:0 0 12px; color:#546470">Điền thông tin người dùng để tạo một tài khoản mới ngay lập tức.</p>
                        <form class="single-account-form">
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
                                <input name="username" placeholder="Tên đăng nhập*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                                <input name="email" type="email" placeholder="Email*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                            </div>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
                                <input name="password" type="password" placeholder="Mật khẩu*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                                <input name="name" placeholder="Họ và tên*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                            </div>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
                                <input name="ten_co_quan" placeholder="Tên cơ quan*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                                <input name="ten_phong_ban" placeholder="Tên phòng ban*" required style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                            </div>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
                                <input name="phone_number" placeholder="Số điện thoại" style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                                <input name="city" placeholder="Thành phố" style="padding:10px; border-radius:4px; border:1px solid #dfe6ea" />
                            </div>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
                                <select name="level_of_education" style="padding:10px; border-radius:4px; border:1px solid #dfe6ea">
                                    <option value="">-- Trình độ học vấn --</option>
                                    <option value="p">Tiến sĩ</option>
                                    <option value="m">Thạc sĩ</option>
                                    <option value="b">Cử nhân</option>
                                    <option value="a">Cao đẳng</option>
                                    <option value="hs">Phổ thông trung học</option>
                                    <option value="jhs">Trung học cơ sở</option>
                                    <option value="el">Tiểu học</option>
                                    <option value="none">Không có bằng cấp chính thức</option>
                                    <option value="other">Khác</option>
                                </select>
                                <select name="gender" style="padding:10px; border-radius:4px; border:1px solid #dfe6ea">
                                    <option value="">-- Giới tính --</option>
                                    <option value="m">Nam</option>
                                    <option value="f">Nữ</option>
                                    <option value="o">Khác/Không muốn tiết lộ</option>
                                </select>
                            </div>
                            <div class="form-message" style="margin-bottom:12px; min-height:20px;"></div>
                            <div style="display:flex; gap:8px;">
                                <button type="button" class="cta-btn cta-primary" data-action="submit-single">Tạo tài khoản</button>
                                <button type="button" class="cta-btn" data-action="cancel-single" style="background:#f1f5f8; color:#1f2d3d;">Hủy</button>
                            </div>
                        </form>
                    `;

                    // Attach submit handler (real API call)
                    const submit = wrap.querySelector('[data-action="submit-single"]');
                    const messageDiv = wrap.querySelector('.form-message');
                    const form = wrap.querySelector('.single-account-form');
                    
                    submit && submit.addEventListener('click', () => {
                        // Get form data
                        const formData = new FormData(form);
                        const data = {};
                        formData.forEach((value, key) => {
                            data[key] = value.trim();
                        });
                        
                        // Validate required fields
                        const requiredFields = ['username', 'email', 'password', 'name', 'ten_co_quan', 'ten_phong_ban'];
                        const missingFields = requiredFields.filter(field => !data[field]);
                        
                        if (missingFields.length > 0) {
                            messageDiv.innerHTML = '<div style="color:#e74c3c; padding:8px; border-radius:4px; background:#fdf2f2; border:1px solid #f5c6cb;">Vui lòng điền đầy đủ thông tin bắt buộc (*)</div>';
                            return;
                        }
                        
                        // Show loading state
                        submit.disabled = true;
                        submit.textContent = 'Đang tạo...';
                        messageDiv.innerHTML = '<div style="color:#3498db; padding:8px; border-radius:4px; background:#eef7ff; border:1px solid #bee5eb;">Đang tạo tài khoản...</div>';
                        
                        // Make API call
                        // Resolve CSRF token from hidden input (if present) or from the csrftoken cookie.
                        const getCsrfFromCookie = () => {
                            const match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
                            return match ? decodeURIComponent(match[2]) : '';
                        };
                        const csrfToken = (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || getCsrfFromCookie();
                        const headers = { 'Content-Type': 'application/json' };
                        if (csrfToken) {
                            headers['X-CSRFToken'] = csrfToken;
                        }

                        fetch('/api/chalix/dashboard/create-single-account/', {
                            method: 'POST',
                            headers: headers,
                            body: JSON.stringify(data)
                        })
                        .then(response => response.json())
                        .then(result => {
                            if (result.success) {
                                messageDiv.innerHTML = `<div style="color:#27ae60; padding:8px; border-radius:4px; background:#eef7f2; border:1px solid #d4edda;">${result.message}</div>`;
                                // Reset form
                                form.reset();
                                setTimeout(() => {
                                    placeholder.innerHTML = `<p style="color:#27ae60;">Đã tạo thành công tài khoản cho <strong>${result.user.name}</strong> (${result.user.username}). Có thể tiếp tục tạo tài khoản khác.</p>`;
                                }, 2000);
                            } else {
                                messageDiv.innerHTML = `<div style="color:#e74c3c; padding:8px; border-radius:4px; background:#fdf2f2; border:1px solid #f5c6cb;">${result.error}</div>`;
                            }
                        })
                        .catch(error => {
                            console.error('Error creating account:', error);
                            messageDiv.innerHTML = '<div style="color:#e74c3c; padding:8px; border-radius:4px; background:#fdf2f2; border:1px solid #f5c6cb;">Có lỗi xảy ra. Vui lòng thử lại.</div>';
                        })
                        .finally(() => {
                            submit.disabled = false;
                            submit.textContent = 'Tạo tài khoản';
                        });
                    });
                    
                    // Cancel button handler
                    const cancel = wrap.querySelector('[data-action="cancel-single"]');
                    cancel && cancel.addEventListener('click', () => {
                        placeholder.innerHTML = '<p>Chọn hành động để bắt đầu: tạo tài khoản đơn lẻ hoặc tạo nhiều tài khoản cùng lúc.</p>';
                    });

                } else if (action === 'bulk') {
                    placeholder.innerHTML = `
                        <h3 style="margin:0 0 8px;">Tạo nhiều tài khoản</h3>
                        <p style="margin:0 0 12px; color:#546470">Tải lên file CSV theo mẫu để tạo nhiều tài khoản cùng lúc.</p>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <input type="file" accept=".csv" />
                            <button type="button" class="cta-btn cta-secondary" data-action="upload-csv">Tải lên</button>
                        </div>
                        <p style="margin-top:12px; color:#8aa3b6; font-size:13px;">(Mô phỏng) Sau khi upload, các hàng hợp lệ sẽ được tạo thành tài khoản.</p>
                    `;

                    const uploadBtn = wrap.querySelector('[data-action="upload-csv"]');
                    uploadBtn && uploadBtn.addEventListener('click', () => {
                        wrap.querySelector('.create-account-placeholder').innerHTML = '<p>CSV đã được xử lý (mô phỏng). Hiển thị kết quả tạo tài khoản...</p>';
                    });
                }
            });
        });
    }

    window.CMS_TABS['create-account'] = {
        render: render
    };

})();
