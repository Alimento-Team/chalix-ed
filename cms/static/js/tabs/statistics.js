/**
 * Statistics Tab Module for CMS Dashboard
 * Vietnamese Learning Management System
 */

(function() {
    'use strict';

    // Ensure CMS_TABS namespace exists
    if (!window.CMS_TABS) {
        window.CMS_TABS = {};
    }

    // Statistics module
    window.CMS_TABS['statistics'] = {
        render: function(container, options) {
            if (!container) {
                console.error('Statistics: Container element is required');
                return;
            }

            const contentTitle = options.contentTitle || 'Thống kê hệ thống';
            const contentDescription = options.contentDescription || 'Xem các thống kê và báo cáo tổng quan về hệ thống học tập.';

            // Clear container
            container.innerHTML = '';

            // Create statistics interface
            const statisticsHTML = `
                <div class="statistics-container">
                    <div class="statistics-header">
                        <h2>${contentTitle}</h2>
                        <p class="statistics-description">${contentDescription}</p>
                    </div>
                    
                    <div class="statistics-filters">
                        <div class="filter-row">
                            <div class="filter-group">
                                <label for="filter-phone">Lọc theo SĐT người học:</label>
                                <input type="text" id="filter-phone" class="form-control" placeholder="Nhập số điện thoại">
                            </div>
                            <div class="filter-group">
                                <label for="filter-name">Lọc theo tên người học:</label>
                                <input type="text" id="filter-name" class="form-control" placeholder="Nhập tên người học">
                            </div>
                        </div>
                        <div class="filter-row">
                            <div class="filter-group">
                                <label for="filter-year">Lọc theo năm:</label>
                                <select id="filter-year" class="form-control">
                                    <option value="">Tất cả năm</option>
                                </select>
                            </div>
                            <div class="filter-group">
                                <label for="filter-completion">Lọc theo tình trạng hoàn thành:</label>
                                <select id="filter-completion" class="form-control">
                                    <option value="">Tất cả</option>
                                    <option value="completed">Đạt (100%)</option>
                                    <option value="80">80%</option>
                                    <option value="60">60%</option>
                                    <option value="50">50%</option>
                                    <option value="under_50">Ít hơn 50%</option>
                                </select>
                            </div>
                        </div>
                        <div class="filter-actions">
                            <button type="button" id="apply-filters" class="btn btn-primary">Áp dụng bộ lọc</button>
                            <button type="button" id="reset-filters" class="btn btn-default">Đặt lại</button>
                            <button type="button" id="export-data" class="btn btn-success">Xuất dữ liệu</button>
                        </div>
                    </div>

                    <div class="statistics-content">
                        <div class="loading-indicator" id="loading-indicator" style="display: none;">
                            <i class="fa fa-spinner fa-spin"></i>
                            <span>Đang tải dữ liệu thống kê...</span>
                        </div>

                        <div class="statistics-summary" id="statistics-summary">
                            <div class="summary-card">
                                <h3>Tổng số người học</h3>
                                <div class="stat-number" id="total-learners">0</div>
                            </div>
                            <div class="summary-card">
                                <h3>Người học đã hoàn thành</h3>
                                <div class="stat-number" id="completed-learners">0</div>
                            </div>
                            <div class="summary-card">
                                <h3>Tỷ lệ hoàn thành</h3>
                                <div class="stat-number" id="completion-rate">0%</div>
                            </div>
                            <div class="summary-card">
                                <h3>Trung bình giờ học</h3>
                                <div class="stat-number" id="average-hours">0</div>
                            </div>
                        </div>

                        <div class="statistics-tables-container">
                            <!-- Table 1: Course completion statistics -->
                            <div class="statistics-table-section">
                                <h3 class="table-section-title">Bảng thống kê 1: Thống kê mỗi khóa học có bao nhiều người học hoàn thành (Sắp xếp theo số học viên giảm dần)</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="course-completion-table">
                                        <thead>
                                            <tr>
                                                <th>TT</th>
                                                <th>Tên khóa học</th>
                                                <th>Số học viên hoàn thành</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr id="no-data-row-1">
                                                <td colspan="3" class="text-center">Không có dữ liệu</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Table 2: Organization completion rate statistics -->
                            <div class="statistics-table-section">
                                <h3 class="table-section-title">Bảng thống kê 2: Thống kê mỗi cơ quan có bao nhiều người học hoàn thành khóa học (Sắp xếp thêm tỷ lệ % giảm dần)</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="organization-completion-table">
                                        <thead>
                                            <tr>
                                                <th>TT</th>
                                                <th>Tên cơ quan</th>
                                                <th>Số học viên</th>
                                                <th>Tỷ lệ % hoàn thành</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr id="no-data-row-2">
                                                <td colspan="4" class="text-center">Không có dữ liệu</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Table 3: Organization courses completed statistics -->
                            <div class="statistics-table-section">
                                <h3 class="table-section-title">Bảng thống kê 3: Thống kê mỗi cơ quan học được bao nhiều khóa học (Sắp xếp số khóa học giảm dần)</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="organization-courses-table">
                                        <thead>
                                            <tr>
                                                <th>TT</th>
                                                <th>Tên cơ quan</th>
                                                <th>Số khóa học đã học</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr id="no-data-row-3">
                                                <td colspan="3" class="text-center">Không có dữ liệu</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <!-- Table 4: Original learner statistics table -->
                        <div class="statistics-table-section">
                            <h3 class="table-section-title">Bảng thống kê 4: Thống kê chi tiết người học</h3>
                            <div class="statistics-table-container">
                                <table class="table table-striped" id="statistics-table">
                                    <thead>
                                        <tr>
                                            <th>STT</th>
                                            <th>Tên người học</th>
                                            <th>Số điện thoại</th>
                                            <th>Năm</th>
                                            <th>Tổng giờ học</th>
                                            <th>Tỷ lệ hoàn thành</th>
                                            <th>Trạng thái</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr id="no-data-row">
                                            <td colspan="7" class="text-center">Không có dữ liệu</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div class="pagination-container" id="pagination-container" style="display: none;">
                            <nav aria-label="Statistics pagination">
                                <ul class="pagination" id="pagination-list">
                                </ul>
                            </nav>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = statisticsHTML;

            // Populate last 3 years (including current year) in the year filter
            try {
                const yearSelect = container.querySelector('#filter-year');
                if (yearSelect) {
                    // Clear existing options except the first (Tất cả năm)
                    yearSelect.innerHTML = '<option value="">Tất cả năm</option>';
                    const currentYear = new Date().getFullYear();
                    for (let i = 0; i < 3; i++) {
                        const y = currentYear - i;
                        const opt = document.createElement('option');
                        opt.value = String(y);
                        opt.textContent = String(y);
                        yearSelect.appendChild(opt);
                    }
                }
            } catch (err) {
                // Non-fatal — continue rendering
                console.warn('Failed to populate year filter', err);
            }

            // Apply CSS styles
            this.applyStyles();

            // Initialize functionality
            this.initializeEventHandlers();

            // Load initial data
            this.loadStatisticsData();
        },

        applyStyles: function() {
            // Check if styles are already applied
            if (document.getElementById('statistics-styles')) {
                return;
            }

            const style = document.createElement('style');
            style.id = 'statistics-styles';
            style.textContent = `
                .statistics-container {
                    padding: 20px;
                    font-family: 'Open Sans', Arial, sans-serif;
                }

                .statistics-header h2 {
                    color: #2c5aa0;
                    margin-bottom: 10px;
                    font-size: 24px;
                    font-weight: 600;
                }

                .statistics-description {
                    color: #666;
                    margin-bottom: 20px;
                    font-size: 14px;
                }

                .statistics-filters {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border: 1px solid #dee2e6;
                }

                .filter-row {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 15px;
                }

                .filter-group {
                    flex: 1;
                }

                .filter-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                    color: #333;
                    font-size: 13px;
                }

                .filter-group input,
                .filter-group select {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 13px;
                }

                .filter-actions {
                    display: flex;
                    gap: 10px;
                    margin-top: 10px;
                }

                .filter-actions .btn {
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 13px;
                    cursor: pointer;
                    border: 1px solid transparent;
                }

                .btn-primary {
                    background-color: #2c5aa0;
                    color: white;
                    border-color: #2c5aa0;
                }

                .btn-primary:hover {
                    background-color: #1e3f73;
                }

                .btn-default {
                    background-color: #f8f9fa;
                    color: #333;
                    border-color: #ccc;
                }

                .btn-default:hover {
                    background-color: #e2e6ea;
                }

                .btn-success {
                    background-color: #28a745;
                    color: white;
                    border-color: #28a745;
                }

                .btn-success:hover {
                    background-color: #218838;
                }

                .loading-indicator {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                }

                .loading-indicator .fa-spinner {
                    margin-right: 10px;
                    font-size: 16px;
                }

                .statistics-summary {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 30px;
                }

                .summary-card {
                    flex: 1;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .summary-card h3 {
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #666;
                    font-weight: 500;
                }

                .summary-card .stat-number {
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c5aa0;
                }

                .statistics-tables-container {
                    display: flex;
                    flex-direction: column;
                    gap: 30px;
                }

                .statistics-table-section {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .table-section-title {
                    color: #2c5aa0;
                    font-size: 16px;
                    font-weight: 600;
                    margin: 0 0 15px 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #2c5aa0;
                }

                .statistics-table-container {
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    overflow-x: auto;
                }

                .statistics-table-container table {
                    width: 100%;
                    margin-bottom: 0;
                    border-collapse: collapse;
                    table-layout: fixed; /* helps keep columns aligned */
                }

                .statistics-table-container th {
                    background-color: #f8f9fa;
                    border-bottom: 2px solid #dee2e6;
                    padding: 12px 12px;
                    font-weight: 600;
                    font-size: 13px;
                    color: #333;
                    text-align: left;
                    vertical-align: middle;
                }

                .statistics-table-container td {
                    padding: 12px 12px;
                    border-bottom: 1px solid #dee2e6;
                    font-size: 13px;
                    vertical-align: middle; /* center content vertically */
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                /* Column widths and alignment */
                .statistics-table-container th:nth-child(1),
                .statistics-table-container td:nth-child(1) { width: 60px; text-align: center; }
                .statistics-table-container th:nth-child(2),
                .statistics-table-container td:nth-child(2) { width: 35%; text-align: left; }
                .statistics-table-container th:nth-child(3),
                .statistics-table-container td:nth-child(3) { width: 15%; text-align: center; }
                .statistics-table-container th:nth-child(4),
                .statistics-table-container td:nth-child(4) { width: 8%; text-align: center; }
                .statistics-table-container th:nth-child(5),
                .statistics-table-container td:nth-child(5) { width: 12%; text-align: center; }
                .statistics-table-container th:nth-child(6),
                .statistics-table-container td:nth-child(6) { width: 10%; text-align: center; }
                .statistics-table-container th:nth-child(7),
                .statistics-table-container td:nth-child(7) { width: 12%; text-align: center; }

                .statistics-table-container tr:hover {
                    background-color: #f8f9fa;
                }

                .completion-status {
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 500;
                    text-align: center;
                }

                .status-completed {
                    background-color: #d4edda;
                    color: #155724;
                }

                .status-high {
                    background-color: #d1ecf1;
                    color: #0c5460;
                }

                .status-medium {
                    background-color: #fff3cd;
                    color: #856404;
                }

                .status-low {
                    background-color: #f8d7da;
                    color: #721c24;
                }

                .pagination-container {
                    margin-top: 20px;
                    display: flex;
                    justify-content: center;
                }

                .pagination {
                    display: flex;
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }

                .pagination li {
                    margin: 0 2px;
                }

                .pagination li a {
                    padding: 8px 12px;
                    text-decoration: none;
                    border: 1px solid #dee2e6;
                    color: #2c5aa0;
                    border-radius: 4px;
                    display: block;
                }

                .pagination li.active a {
                    background-color: #2c5aa0;
                    color: white;
                }

                .pagination li a:hover {
                    background-color: #f8f9fa;
                }

                @media (max-width: 768px) {
                    .filter-row {
                        flex-direction: column;
                        gap: 10px;
                    }

                    .statistics-summary {
                        flex-direction: column;
                        gap: 15px;
                    }

                    .filter-actions {
                        flex-direction: column;
                    }
                }
            `;
            document.head.appendChild(style);
        },

        initializeEventHandlers: function() {
            const self = this;

            // Apply filters button
            document.getElementById('apply-filters').addEventListener('click', function() {
                self.loadStatisticsData();
            });

            // Reset filters button
            document.getElementById('reset-filters').addEventListener('click', function() {
                document.getElementById('filter-phone').value = '';
                document.getElementById('filter-name').value = '';
                document.getElementById('filter-year').value = '';
                document.getElementById('filter-completion').value = '';
                self.loadStatisticsData();
            });

            // Export data button
            document.getElementById('export-data').addEventListener('click', function() {
                self.exportStatisticsData();
            });

            // Enter key support for filters
            document.getElementById('filter-phone').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    self.loadStatisticsData();
                }
            });

            document.getElementById('filter-name').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    self.loadStatisticsData();
                }
            });
        },

        loadStatisticsData: function(page = 1) {
            const loadingIndicator = document.getElementById('loading-indicator');
            const statisticsContent = document.querySelector('.statistics-content');
            
            // Show loading
            loadingIndicator.style.display = 'block';

            // Collect filter values
            const filters = {
                phone: document.getElementById('filter-phone').value.trim(),
                name: document.getElementById('filter-name').value.trim(),
                year: document.getElementById('filter-year').value,
                completion: document.getElementById('filter-completion').value,
                page: page
            };

            // Make API call to get statistics data
            const apiUrl = '/api/chalix/dashboard/api/';
            const params = new URLSearchParams({
                tab: 'statistics',
                ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
            });

            fetch(`${apiUrl}?${params}`, {
                method: 'GET',
                credentials: 'same-origin', // ensure cookies (session) are sent
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            })
            .then(response => {
                // If server returned a redirect to login or an error page, it's likely HTML.
                const contentType = response.headers.get('content-type') || '';
                if (!response.ok) {
                    // Try to show a helpful message for common statuses
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Authentication required. Please sign in.');
                    }
                    if (response.status === 404) {
                        throw new Error('Endpoint not found (404).');
                    }
                    throw new Error('Server returned status ' + response.status);
                }

                if (contentType.indexOf('application/json') === -1) {
                    // Not JSON - read text and include a snippet in the error to help debugging
                    return response.text().then(text => {
                        const preview = text.substring(0, 300).replace(/\s+/g, ' ');
                        throw new Error('Expected JSON but got HTML/text. Server response preview: ' + preview);
                    });
                }

                return response.json();
            })
            .then(data => {
                loadingIndicator.style.display = 'none';
                this.renderStatisticsData(data);
            })
            .catch(error => {
                loadingIndicator.style.display = 'none';
                console.error('Error loading statistics:', error);
                this.showError(error.message || 'Có lỗi xảy ra khi tải dữ liệu thống kê. Vui lòng thử lại.');
            });
        },

        renderStatisticsData: function(data) {
            // Update summary cards
            document.getElementById('total-learners').textContent = data.summary.total_learners || 0;
            document.getElementById('completed-learners').textContent = data.summary.completed_learners || 0;
            document.getElementById('completion-rate').textContent = `${data.summary.completion_rate || 0}%`;
            document.getElementById('average-hours').textContent = data.summary.average_hours || 0;

            // Animate numbers
            this.animateNumbers();

            // Update three tables
            this.updateCourseCompletionTable(data.course_completions || []);
            this.updateOrganizationCompletionTable(data.organization_completions || []);
            this.updateOrganizationCoursesTable(data.organization_courses || []);

            // Update the 4th table (original learner statistics)
            this.updateStatisticsTable(data.learners || []);

            // Update pagination for the 4th table
            this.updatePagination(data.pagination || {});
        },

        updateCourseCompletionTable: function(courses) {
            const tableBody = document.querySelector('#course-completion-table tbody');
            
            if (!courses || courses.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row-1"><td colspan="3" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            courses.forEach((course, index) => {
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${course.course_name || 'N/A'}</td>
                        <td>${course.completed_count || 0}</td>
                    </tr>
                `;
            });

            tableBody.innerHTML = html;
        },

        updateOrganizationCompletionTable: function(organizations) {
            const tableBody = document.querySelector('#organization-completion-table tbody');
            
            if (!organizations || organizations.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row-2"><td colspan="4" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            organizations.forEach((org, index) => {
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${org.organization_name || 'N/A'}</td>
                        <td>${org.learner_count || 0}</td>
                        <td>${org.completion_percentage || 0}%</td>
                    </tr>
                `;
            });

            tableBody.innerHTML = html;
        },

        updateOrganizationCoursesTable: function(organizations) {
            const tableBody = document.querySelector('#organization-courses-table tbody');
            
            if (!organizations || organizations.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row-3"><td colspan="3" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            organizations.forEach((org, index) => {
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${org.organization_name || 'N/A'}</td>
                        <td>${org.courses_count || 0}</td>
                    </tr>
                `;
            });

            tableBody.innerHTML = html;
        },

        updateStatisticsTable: function(learners) {
            const tableBody = document.querySelector('#statistics-table tbody');
            
            if (!learners || learners.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row"><td colspan="7" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            learners.forEach((learner, index) => {
                const statusClass = this.getStatusClass(learner.completion_percentage);
                const statusText = this.getStatusText(learner.completion_percentage);
                
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${learner.name || 'N/A'}</td>
                        <td>${learner.phone || 'N/A'}</td>
                        <td>${learner.year || 'N/A'}</td>
                        <td>${learner.total_hours || 0} giờ</td>
                        <td>${learner.completion_percentage || 0}%</td>
                        <td><span class="completion-status ${statusClass}">${statusText}</span></td>
                    </tr>
                `;
            });

            tableBody.innerHTML = html;
        },

        getStatusClass: function(percentage) {
            if (percentage >= 100) return 'status-completed';
            if (percentage >= 80) return 'status-high';
            if (percentage >= 50) return 'status-medium';
            return 'status-low';
        },

        getStatusText: function(percentage) {
            if (percentage >= 100) return 'Đạt (100%)';
            if (percentage >= 80) return '80%';
            if (percentage >= 60) return '60%';
            if (percentage >= 50) return '50%';
            return 'Ít hơn 50%';
        },

        updatePagination: function(pagination) {
            const paginationContainer = document.getElementById('pagination-container');
            const paginationList = document.getElementById('pagination-list');
            
            if (!pagination.total_pages || pagination.total_pages <= 1) {
                paginationContainer.style.display = 'none';
                return;
            }

            paginationContainer.style.display = 'block';
            
            let html = '';
            const currentPage = pagination.current_page || 1;
            const totalPages = pagination.total_pages;

            // Previous button
            if (currentPage > 1) {
                html += `<li><a href="#" onclick="window.CMS_TABS.statistics.loadStatisticsData(${currentPage - 1}); return false;">‹</a></li>`;
            }

            // Page numbers
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                const activeClass = i === currentPage ? 'active' : '';
                html += `<li class="${activeClass}"><a href="#" onclick="window.CMS_TABS.statistics.loadStatisticsData(${i}); return false;">${i}</a></li>`;
            }

            // Next button
            if (currentPage < totalPages) {
                html += `<li><a href="#" onclick="window.CMS_TABS.statistics.loadStatisticsData(${currentPage + 1}); return false;">›</a></li>`;
            }

            paginationList.innerHTML = html;
        },

        animateNumbers: function() {
            const numbers = document.querySelectorAll('.stat-number');
            numbers.forEach(element => {
                const targetValue = parseInt(element.textContent) || 0;
                this.animateNumber(element, 0, targetValue, 1000);
            });
        },

        animateNumber: function(element, start, end, duration) {
            const startTime = Date.now();
            const isPercentage = element.textContent.includes('%');
            
            function updateNumber() {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const easedProgress = 1 - Math.pow(1 - progress, 3);
                const currentValue = Math.floor(start + ((end - start) * easedProgress));
                
                element.textContent = isPercentage ? `${currentValue}%` : currentValue.toLocaleString('vi-VN');

                if (progress < 1) {
                    requestAnimationFrame(updateNumber);
                }
            }

            updateNumber();
        },

        exportStatisticsData: function() {
            // Get current filter parameters
            const filters = {
                phone: document.getElementById('filter-phone').value.trim(),
                name: document.getElementById('filter-name').value.trim(),
                year: document.getElementById('filter-year').value,
                completion: document.getElementById('filter-completion').value,
                export: 'csv'
            };

            // Create download URL
            const apiUrl = '/api/chalix/dashboard/api/';
            const params = new URLSearchParams({
                tab: 'statistics',
                ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
            });

            // Create temporary link to trigger download
            const link = document.createElement('a');
            link.href = `${apiUrl}?${params}`;
            link.download = `thong-ke-nguoi-hoc-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        getCSRFToken: function() {
            // Get CSRF token from cookie
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
            return cookieValue || '';
        },

        showError: function(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-error';
            errorDiv.style.cssText = `
                background-color: #f8d7da;
                color: #721c24;
                padding: 12px;
                border-radius: 4px;
                margin: 20px 0;
                border: 1px solid #f5c6cb;
            `;
            errorDiv.textContent = message;
            
            const container = document.querySelector('.statistics-container');
            container.insertBefore(errorDiv, container.firstChild);
            
            // Remove error after 5 seconds
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 5000);
        }
    };

    console.log('Statistics tab module loaded');
})();