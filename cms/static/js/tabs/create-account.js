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
            @media (max-width:520px){ .cta-btn{ width:100%; min-width:0; } .create-account-cta{flex-direction:column;} }
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
                            <div style="display:flex; gap:8px; flex-wrap:wrap">
                                <input name="username" placeholder="Tên đăng nhập" style="flex:1; padding:8px; border-radius:4px; border:1px solid #dfe6ea" />
                                <input name="email" placeholder="Email" style="flex:1; padding:8px; border-radius:4px; border:1px solid #dfe6ea" />
                            </div>
                            <div style="margin-top:10px; display:flex; gap:8px;">
                                <button type="button" class="cta-btn cta-primary" data-action="submit-single">Tạo</button>
                                <button type="button" class="cta-btn" data-action="cancel-single" style="background:#f1f5f8; color:#1f2d3d;">Hủy</button>
                            </div>
                        </form>
                    `;

                    // attach submit handler (mock)
                    const submit = wrap.querySelector('[data-action="submit-single"]');
                    submit && submit.addEventListener('click', () => {
                        const u = wrap.querySelector('input[name="username"]').value || '(không có)';
                        const e = wrap.querySelector('input[name="email"]').value || '(không có)';
                        wrap.querySelector('.create-account-placeholder').innerHTML = `<p>Đã gửi tạo tài khoản: <strong>${u}</strong> (${e}). Đây là mô phỏng; tích hợp backend cần được thực hiện.</p>`;
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
