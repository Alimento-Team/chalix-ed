/**
 * Approve Requests Tab Module for CMS Dashboard
 * Renders course-topic emotion adjustment statistics.
 */

(function() {
    'use strict';

    if (!window.CMS_TABS) {
        window.CMS_TABS = {};
    }

    window.CMS_TABS['approve-requests'] = {
        render: function(container, options) {
            if (!container) {
                return;
            }

            const contentTitle = options.contentTitle || 'Phê duyệt yêu cầu';
            const contentDescription = options.contentDescription || 'Thống kê điều chỉnh chương trình học theo cảm xúc người học.';

            container.innerHTML = `
                <div class="approve-requests-container">
                    <div class="approve-requests-header">
                        <h2>${contentTitle}</h2>
                        <p class="approve-requests-description">${contentDescription}</p>
                    </div>

                    <div id="approve-requests-loading" class="approve-requests-loading">
                        <i class="fa fa-spinner fa-spin" aria-hidden="true"></i>
                        Đang tải dữ liệu...
                    </div>

                    <div id="approve-requests-error" class="approve-requests-error" style="display:none;"></div>

                    <div id="approve-requests-content" style="display:none;">
                        <div class="approve-requests-summary" id="approve-requests-summary"></div>
                        <div class="approve-requests-table-wrapper" id="approve-requests-table-wrapper"></div>
                    </div>
                </div>
            `;

            this.applyStyles();
            this.loadData();
        },

        loadData: function() {
            const loadingEl = document.getElementById('approve-requests-loading');
            const errorEl = document.getElementById('approve-requests-error');
            const contentEl = document.getElementById('approve-requests-content');

            fetch('/api/chalix/dashboard/api/?tab=approve-requests', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
            })
                .then(async (response) => {
                    if (!response.ok) {
                        const text = await response.text();
                        throw new Error(text || `HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    if (loadingEl) {
                        loadingEl.style.display = 'none';
                    }
                    if (contentEl) {
                        contentEl.style.display = 'block';
                    }
                    this.renderData(data || {});
                })
                .catch((error) => {
                    if (loadingEl) {
                        loadingEl.style.display = 'none';
                    }
                    if (errorEl) {
                        errorEl.style.display = 'block';
                        errorEl.textContent = 'Không thể tải dữ liệu phê duyệt yêu cầu.';
                    }
                    // Keep detailed error in console for debugging.
                    console.error('[Approve Requests] Failed to load data', error);
                });
        },

        renderData: function(data) {
            const summaryEl = document.getElementById('approve-requests-summary');
            const tableWrapperEl = document.getElementById('approve-requests-table-wrapper');
            if (!summaryEl || !tableWrapperEl) {
                return;
            }

            const courses = data.courses || [];
            const topicHeaders = data.topic_headers || [];

            summaryEl.innerHTML = `
                <div class="approve-summary-card">
                    <strong>Tổng số khóa học:</strong> ${data.total_courses || 0}
                </div>
                <div class="approve-summary-card warn">
                    <strong>Số khóa cần điều chỉnh:</strong> ${data.adjust_courses || 0}
                </div>
            `;

            if (!courses.length || !topicHeaders.length) {
                tableWrapperEl.innerHTML = '<div class="approve-empty">Không có dữ liệu để hiển thị.</div>';
                return;
            }

            const groupedHeader = topicHeaders
                .map((header) => `<th colspan="3">${this.escapeHtml(header.display_name)}</th>`)
                .join('');

            const groupedSubHeader = topicHeaders
                .map(() => '<th>Thích</th><th>Bình thường</th><th>Không thích</th>')
                .join('');

            const rowsHtml = courses.map((course, index) => {
                const topicCells = (course.topic_stats || [])
                    .map((topic) => {
                        return `
                            <td>${topic.like_count || 0}</td>
                            <td>${topic.neutral_count || 0}</td>
                            <td>${topic.dislike_count || 0}</td>
                        `;
                    })
                    .join('');

                const recommendationClass = course.needs_adjustment ? 'recommendation recommendation-alert' : 'recommendation';

                return `
                    <tr>
                        <td>${index + 1}</td>
                        <td class="course-name">${this.escapeHtml(course.course_name || 'N/A')}</td>
                        ${topicCells}
                        <td class="${recommendationClass}">${this.escapeHtml(course.recommendation || '')}</td>
                    </tr>
                `;
            }).join('');

            tableWrapperEl.innerHTML = `
                <table class="approve-requests-table">
                    <thead>
                        <tr>
                            <th>TT</th>
                            <th>Tên khóa học</th>
                            ${groupedHeader}
                            <th rowspan="2">Gợi ý điều chỉnh khóa học</th>
                        </tr>
                        <tr>
                            <th></th>
                            <th></th>
                            ${groupedSubHeader}
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            `;
        },

        getCSRFToken: function() {
            const match = document.cookie.match(/csrftoken=([^;]+)/);
            return match ? decodeURIComponent(match[1]) : '';
        },

        escapeHtml: function(value) {
            if (value === null || value === undefined) {
                return '';
            }
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        },

        applyStyles: function() {
            if (document.getElementById('approve-requests-styles')) {
                return;
            }

            const style = document.createElement('style');
            style.id = 'approve-requests-styles';
            style.textContent = `
                .approve-requests-container { padding: 20px; }
                .approve-requests-header h2 { color: #2c5aa0; margin-bottom: 6px; }
                .approve-requests-description { color: #666; margin-bottom: 16px; }
                .approve-requests-loading { padding: 18px; color: #555; }
                .approve-requests-error { padding: 14px; border-radius: 6px; background: #f8d7da; color: #721c24; }
                .approve-requests-summary { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
                .approve-summary-card { padding: 10px 14px; border: 1px solid #d7dce1; border-radius: 8px; background: #fff; }
                .approve-summary-card.warn { border-color: #f4c7cc; background: #fff6f7; }
                .approve-requests-table-wrapper { overflow-x: auto; }
                .approve-requests-table { width: 100%; border-collapse: collapse; min-width: 900px; }
                .approve-requests-table th, .approve-requests-table td { border: 1px solid #d9d9d9; padding: 8px; }
                .approve-requests-table thead th { background: #f1f4f8; text-align: center; }
                .approve-requests-table td { text-align: center; }
                .approve-requests-table td.course-name { text-align: left; min-width: 180px; }
                .approve-requests-table td.recommendation { text-align: left; min-width: 200px; }
                .approve-requests-table td.recommendation-alert { color: #c62828; font-weight: 700; }
                .approve-empty { padding: 20px; text-align: center; color: #6b7280; border: 1px dashed #d1d5db; border-radius: 8px; }
            `;
            document.head.appendChild(style);
        },
    };
})();
