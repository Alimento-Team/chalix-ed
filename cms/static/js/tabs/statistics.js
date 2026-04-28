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

            // Check user role
            const roleData = window.CMS_ROLE_DATA || {};
            const userRole = options.user_role || roleData.user_role_code || roleData.user_role || '';
            const isAgencyUser = userRole === 'co_quan';

            // Create statistics interface
            const statisticsHTML = `
                <div class="statistics-container">
                    <div class="statistics-header">
                        <h2>${contentTitle}</h2>
                        <p class="statistics-description">${contentDescription}</p>
                        
                        ${`
                        <div class="statistics-toolbar">
                            <div class="statistics-year-filter">
                                <label for="filter-year">Năm</label>
                                <select id="filter-year" class="year-dropdown" aria-label="Lọc theo năm">
                                    <option value="2026" selected>2026</option>
                                </select>
                            </div>
                        </div>
                        `}

                        <!-- Table navigation buttons -->
                        <div class="statistics-nav-buttons">
                            ${isAgencyUser ? `
                            <button class="stat-nav-btn active" data-table="statistics-table-section-1">
                                <i class="fa fa-clock-o"></i>
                                <span>Giờ học công chức</span>
                            </button>
                            <button class="stat-nav-btn" data-table="statistics-table-section-2">
                                <i class="fa fa-users"></i>
                                <span>Người học khóa học</span>
                            </button>
                            ` : `
                            <button class="stat-nav-btn active" data-table="statistics-table-section-1">
                                <i class="fa fa-building"></i>
                                <span>Người học theo cơ quan</span>
                            </button>
                            <button class="stat-nav-btn" data-table="statistics-table-section-2">
                                <i class="fa fa-users"></i>
                                <span>Người học khóa học</span>
                            </button>
                            <button class="stat-nav-btn" data-table="statistics-table-section-3">
                                <i class="fa fa-graduation-cap"></i>
                                <span>Khóa học theo cơ quan</span>
                            </button>
                            <button class="stat-nav-btn" data-table="statistics-table-section-4">
                                <i class="fa fa-clock-o"></i>
                                <span>Giờ học công chức</span>
                            </button>
                            `}
                        </div>
                    </div>
                    <div class="statistics-content">
                        <div class="statistics-tables-container">
                            ${isAgencyUser ? `
                            <!-- Co Quan sees only 2 tables for their organization -->
                            <div class="statistics-table-section" id="statistics-table-section-1">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ GIỜ HỌC CỦA CÔNG CHỨC, VIÊN CHỨC">THỐNG KÊ SỐ GIỜ HỌC CỦA CÔNG CHỨC, VIÊN CHỨC NĂM 2026</h3>
                                
                                <!-- Search and Filter Controls -->
                                <div class="statistics-filters">
                                    <div class="filter-row">
                                        <div class="filter-group">
                                            <label for="filter-search-id">Tìm kiếm theo ID/Tên:</label>
                                            <input type="text" id="filter-search-id" class="form-control" placeholder="Nhập ID hoặc tên người học..." />
                                        </div>
                                    </div>
                                </div>

                                <!-- Pagination Top -->
                                <div id="pagination-container-top" style="display: none; text-align: center; margin-bottom: 15px;">
                                    <ul id="pagination-list-top" class="pagination" style="display: inline-block; list-style: none; padding: 0;"></ul>
                                </div>

                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="statistics-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
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

                                <!-- Pagination Bottom -->
                                <div id="pagination-container" style="display: none; text-align: center; margin-top: 15px;">
                                    <ul id="pagination-list" class="pagination" style="display: inline-block; list-style: none; padding: 0;"></ul>
                                </div>
                            </div>
                            <div class="statistics-table-section">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC KHÓA HỌC">THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC KHÓA HỌC NĂM 2025</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="course-completion-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
                                                <th>Tên khóa học</th>
                                                <th>Số người đang học</th>
                                                <th>Số học viên hoàn thành</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr id="no-data-row-1">
                                                <td colspan="4" class="text-center">Không có dữ liệu</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            ` : `
                            <!-- Bo and other roles see all 4 tables -->
                            <div class="statistics-table-section" id="statistics-table-section-1">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ NGƯỜI HỌC THEO CƠ QUAN">THỐNG KÊ SỐ NGƯỜI HỌC THEO CƠ QUAN NĂM 2025</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="organization-completion-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
                                                <th>Tên cơ quan</th>
                                                <th>Số người học</th>
                                                <th>Tỷ lệ hoàn thành</th>
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
                            <div class="statistics-table-section" id="statistics-table-section-2">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC KHÓA HỌC">THỐNG KÊ SỐ NGƯỜI HỌC CỦA CÁC KHÓA HỌC NĂM 2025</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="course-completion-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
                                                <th>Tên khóa học</th>
                                                <th>Số người đang học</th>
                                                <th>Số học viên hoàn thành</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr id="no-data-row-1">
                                                <td colspan="4" class="text-center">Không có dữ liệu</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="statistics-table-section" id="statistics-table-section-3">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ KHÓA HỌC THEO CƠ QUAN">THỐNG KÊ SỐ KHÓA HỌC THEO CƠ QUAN NĂM 2025</h3>
                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="organization-courses-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
                                                <th>Tên cơ quan</th>
                                                <th>Số khóa học</th>
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
                            <div class="statistics-table-section" id="statistics-table-section-4">
                                <h3 class="table-section-title" data-base-title="THỐNG KÊ SỐ GIỜ HỌC CỦA CÔNG CHỨC, VIÊN CHỨC">THỐNG KÊ SỐ GIỜ HỌC CỦA CÔNG CHỨC, VIÊN CHỨC NĂM 2026</h3>
                                
                                <!-- Search and Filter Controls -->
                                <div class="statistics-filters">
                                    <div class="filter-row">
                                        <div class="filter-group">
                                            <label for="filter-search-id">Tìm kiếm theo ID/Tên:</label>
                                            <input type="text" id="filter-search-id" class="form-control" placeholder="Nhập ID hoặc tên người học..." />
                                        </div>
                                    </div>
                                </div>

                                <!-- Pagination Top -->
                                <div id="pagination-container-top" style="display: none; text-align: center; margin-bottom: 15px;">
                                    <ul id="pagination-list-top" class="pagination" style="display: inline-block; list-style: none; padding: 0;"></ul>
                                </div>

                                <div class="statistics-table-container">
                                    <table class="table table-striped" id="statistics-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 30px; padding: 12px 4px;">TT</th>
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

                                <!-- Pagination Bottom -->
                                <div id="pagination-container" style="display: none; text-align: center; margin-top: 15px;">
                                    <ul id="pagination-list" class="pagination" style="display: inline-block; list-style: none; padding: 0;"></ul>
                                </div>
                            </div>
                            `}
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML = statisticsHTML;

            // Statistics requirement: fixed display year is 2026.
            try {
                const yearSelect = container.querySelector('#filter-year');
                if (yearSelect) {
                    yearSelect.innerHTML = '';
                    const fixedYear = '2026';
                    const opt = document.createElement('option');
                    opt.value = fixedYear;
                    opt.textContent = fixedYear;
                    yearSelect.appendChild(opt);
                    yearSelect.value = fixedYear;
                }
            } catch (err) {
                // Non-fatal — continue rendering
                // debug removed
            }

            this.updateSectionTitles();

            // Apply CSS styles
            this.applyStyles();

            // Initialize table navigation
            this.initializeTableNavigation();

            // Initialize functionality
            this.initializeEventHandlers();

            // Load initial data
            this.loadStatisticsData();
        },

        initializeTableNavigation: function() {
            const self = this;
            const navButtons = document.querySelectorAll('.stat-nav-btn');
            const tableSections = document.querySelectorAll('.statistics-table-section');
            
            // Hide all tables except the first one
            tableSections.forEach((section, index) => {
                if (index === 0) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
            
            // Add click handlers to buttons
            navButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const targetTableId = this.getAttribute('data-table');
                    
                    // Remove active class from all buttons
                    navButtons.forEach(btn => btn.classList.remove('active'));
                    
                    // Add active class to clicked button
                    this.classList.add('active');
                    
                    // Hide all tables
                    tableSections.forEach(section => {
                        section.style.display = 'none';
                    });
                    
                    // Show the target table
                    const targetTable = document.getElementById(targetTableId);
                    if (targetTable) {
                        targetTable.style.display = 'block';
                    }
                });
            });
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

                .statistics-nav-buttons {
                    display: flex;
                    gap: 12px;
                    margin-top: 20px;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                }

                .statistics-toolbar {
                    display: flex;
                    justify-content: flex-end;
                    margin-top: 8px;
                    margin-bottom: 14px;
                }

                .statistics-year-filter {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .statistics-year-filter label {
                    font-weight: 600;
                    color: #2c5aa0;
                    margin: 0;
                }

                .statistics-year-filter .year-dropdown {
                    min-width: 130px;
                    padding: 8px 12px;
                    border: 1px solid #9fb8d8;
                    border-radius: 6px;
                    background: #fff;
                    color: #2c5aa0;
                    font-weight: 600;
                }

                .stat-nav-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 20px;
                    background: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    color: #555;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }

                .stat-nav-btn i {
                    font-size: 16px;
                    color: #777;
                }

                .stat-nav-btn:hover {
                    background: #f8f9fa;
                    border-color: #3494c8;
                    color: #2c5aa0;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }

                .stat-nav-btn:hover i {
                    color: #3494c8;
                }

                .stat-nav-btn.active {
                    background: #3494c8;
                    border-color: #3494c8;
                    color: #ffffff;
                    box-shadow: 0 4px 8px rgba(52, 148, 200, 0.3);
                }

                .stat-nav-btn.active i {
                    color: #ffffff;
                }

                .stat-nav-btn:focus {
                    outline: none;
                    box-shadow: 0 0 0 3px rgba(52, 148, 200, 0.2);
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
                    margin-bottom: 20px;
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

                /* Column widths and alignment - Tables 1, 2, 3 (TT column very narrow) */
                #course-completion-table th:nth-child(1),
                #course-completion-table td:nth-child(1),
                #organization-completion-table th:nth-child(1),
                #organization-completion-table td:nth-child(1),
                #organization-courses-table th:nth-child(1),
                #organization-courses-table td:nth-child(1) { width: 30px; text-align: center; padding: 12px 4px; }

                /* Table 1: Course Completion */
                #course-completion-table th:nth-child(2),
                #course-completion-table td:nth-child(2) { width: 45%; text-align: left; }
                #course-completion-table th:nth-child(3),
                #course-completion-table td:nth-child(3) { width: 18%; text-align: center; }
                #course-completion-table th:nth-child(4),
                #course-completion-table td:nth-child(4) { width: 17%; text-align: center; }

                /* Table 2: Organization Completion */
                #organization-completion-table th:nth-child(2),
                #organization-completion-table td:nth-child(2) { width: 40%; text-align: left; }
                #organization-completion-table th:nth-child(3),
                #organization-completion-table td:nth-child(3) { width: 15%; text-align: center; }
                #organization-completion-table th:nth-child(4),
                #organization-completion-table td:nth-child(4) { width: 15%; text-align: center; }

                /* Table 3: Organization Courses */
                #organization-courses-table th:nth-child(2),
                #organization-courses-table td:nth-child(2) { width: 50%; text-align: left; }
                #organization-courses-table th:nth-child(3),
                #organization-courses-table td:nth-child(3) { width: 20%; text-align: center; }

                /* Table 4: Statistics (STT column narrow) */
                #statistics-table th:nth-child(1),
                #statistics-table td:nth-child(1) { width: 30px; text-align: center; padding: 12px 4px; }
                #statistics-table th:nth-child(2),
                #statistics-table td:nth-child(2) { width: 18%; text-align: left; }
                #statistics-table th:nth-child(3),
                #statistics-table td:nth-child(3) { width: 15%; text-align: center; }
                #statistics-table th:nth-child(4),
                #statistics-table td:nth-child(4) { width: 10%; text-align: center; }
                #statistics-table th:nth-child(5),
                #statistics-table td:nth-child(5) { width: 12%; text-align: center; }
                #statistics-table th:nth-child(6),
                #statistics-table td:nth-child(6) { width: 12%; text-align: center; }
                #statistics-table th:nth-child(7),
                #statistics-table td:nth-child(7) { width: 13%; text-align: center; }

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

                    .statistics-nav-buttons {
                        flex-direction: column;
                        gap: 8px;
                    }

                    .stat-nav-btn {
                        width: 100%;
                        justify-content: center;
                    }
                }

                @media (max-width: 480px) {
                    .stat-nav-btn span {
                        font-size: 12px;
                    }

                    .stat-nav-btn {
                        padding: 10px 16px;
                    }
                }

                /* Pagination Styles */
                #pagination-container, #pagination-container-top {
                    display: none;
                    text-align: center;
                    margin: 20px 0;
                }

                .pagination {
                    list-style: none;
                    padding: 0;
                    margin: 0;
                    display: inline-block;
                }

                .pagination li {
                    display: inline-block;
                    margin: 0 3px;
                }

                .pagination a {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    background-color: #ffffff;
                    color: #333;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: all 0.2s ease;
                }

                .pagination a:hover {
                    background-color: #e9ecef;
                    color: #333;
                    border-color: #3494c8;
                }

                .pagination li.active a {
                    background-color: #3494c8;
                    color: white;
                    border-color: #3494c8;
                }

                /* Search Input Styles */
                .statistics-filters .filter-group {
                    margin-bottom: 0;
                }

                .statistics-filters .filter-group input[type="text"] {
                    width: 100%;
                    max-width: 400px;
                }
            `;
            document.head.appendChild(style);
        },

        initializeEventHandlers: function() {
            const self = this;

            // Apply filters button
            const applyFiltersBtn = document.getElementById('apply-filters');
            if (applyFiltersBtn) {
                applyFiltersBtn.addEventListener('click', function() {
                    self.loadStatisticsData();
                });
            }

            // Reset filters button
            const resetFiltersBtn = document.getElementById('reset-filters');
            if (resetFiltersBtn) {
                resetFiltersBtn.addEventListener('click', function() {
                    const phoneInput = document.getElementById('filter-phone');
                    const nameInput = document.getElementById('filter-name');
                    const yearSelect = document.getElementById('filter-year');
                    const completionSelect = document.getElementById('filter-completion');

                    if (phoneInput) phoneInput.value = '';
                    if (nameInput) nameInput.value = '';
                    if (yearSelect) {
                        yearSelect.value = '2026';
                    }
                    if (completionSelect) completionSelect.value = '';

                    self.updateSectionTitles();
                    self.loadStatisticsData();
                });
            }

            // Export data button
            const exportBtn = document.getElementById('export-data');
            if (exportBtn) {
                exportBtn.addEventListener('click', function() {
                    self.exportStatisticsData();
                });
            }

            // Enter key support for filters
            const phoneInput = document.getElementById('filter-phone');
            if (phoneInput) {
                phoneInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        self.loadStatisticsData();
                    }
                });
            }

            const nameInput = document.getElementById('filter-name');
            if (nameInput) {
                nameInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        self.loadStatisticsData();
                    }
                });
            }

            const searchIdInput = document.getElementById('filter-search-id');
            if (searchIdInput) {
                searchIdInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        self.loadStatisticsData();
                    }
                });
            }

            const yearSelect = document.getElementById('filter-year');
            if (yearSelect) {
                yearSelect.addEventListener('change', function() {
                    self.updateSectionTitles();
                    self.loadStatisticsData();
                });
            }
        },

        loadStatisticsData: function(page = 1) {
            const loadingIndicator = document.getElementById('loading-indicator');
            const statisticsContent = document.querySelector('.statistics-content');
            
            // Show loading when the indicator exists
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }

            this.renderLoadingState();

            // Collect filter values
            const filters = {
                phone: (document.getElementById('filter-phone')?.value || '').trim(),
                name: (document.getElementById('filter-name')?.value || '').trim(),
                student_id: (document.getElementById('filter-search-id')?.value || '').trim(),
                year: document.getElementById('filter-year')?.value || '',
                completion: document.getElementById('filter-completion')?.value || '',
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
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                this.renderStatisticsData(data);
            })
            .catch(error => {
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                console.error('Error loading statistics:', error);
                this.showError(error.message || 'Có lỗi xảy ra khi tải dữ liệu thống kê. Vui lòng thử lại.');
            });
        },

        renderLoadingState: function() {
            const loadingRow = '<tr><td colspan="7" class="text-center"><i class="fa fa-spinner fa-spin"></i> Đang tải dữ liệu...</td></tr>';
            const loadingRow4 = '<tr><td colspan="4" class="text-center"><i class="fa fa-spinner fa-spin"></i> Đang tải dữ liệu...</td></tr>';
            const loadingRow3 = '<tr><td colspan="3" class="text-center"><i class="fa fa-spinner fa-spin"></i> Đang tải dữ liệu...</td></tr>';

            const mainTableBody = document.querySelector('#statistics-table tbody');
            if (mainTableBody) {
                mainTableBody.innerHTML = loadingRow;
            }

            const courseTableBody = document.querySelector('#course-completion-table tbody');
            if (courseTableBody) {
                courseTableBody.innerHTML = loadingRow4;
            }

            const orgCompletionBody = document.querySelector('#organization-completion-table tbody');
            if (orgCompletionBody) {
                orgCompletionBody.innerHTML = loadingRow4;
            }

            const orgCoursesBody = document.querySelector('#organization-courses-table tbody');
            if (orgCoursesBody) {
                orgCoursesBody.innerHTML = loadingRow3;
            }
        },

        renderStatisticsData: function(data) {
            // Debug logging removed in production
            this.updateSectionTitles();
            
            // Update summary cards
            const totalLearners = document.getElementById('total-learners');
            const completedLearners = document.getElementById('completed-learners');
            const completionRate = document.getElementById('completion-rate');
            const averageHours = document.getElementById('average-hours');

            if (totalLearners) totalLearners.textContent = data.summary?.total_learners || 0;
            if (completedLearners) completedLearners.textContent = data.summary?.completed_learners || 0;
            if (completionRate) completionRate.textContent = `${data.summary?.completion_rate || 0}%`;
            if (averageHours) averageHours.textContent = data.summary?.average_hours || 0;

            // Animate numbers when summary cards exist
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
            if (!tableBody) return;
            
            if (!courses || courses.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row-1"><td colspan="4" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            courses.forEach((course, index) => {
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${course.course_name || 'N/A'}</td>
                        <td>${course.current_learners || 0}</td>
                        <td>${course.completed_count || 0}</td>
                    </tr>
                `;
            });

            tableBody.innerHTML = html;
        },

        updateOrganizationCompletionTable: function(organizations) {
            const tableBody = document.querySelector('#organization-completion-table tbody');
            if (!tableBody) return;
            
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
            if (!tableBody) return;
            
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
            if (!tableBody) return;
            
            if (!learners || learners.length === 0) {
                tableBody.innerHTML = '<tr id="no-data-row"><td colspan="7" class="text-center">Không có dữ liệu</td></tr>';
                return;
            }

            let html = '';
            learners.forEach((learner, index) => {
                const learnerName = this.escapeHtml(learner.name || 'N/A');
                const totalStudiedTime = learner.total_studied_time ?? learner.total_hours ?? 0;
                const completedPercentage = learner.completed_percentage ?? learner.completion_percentage ?? 0;
                const status = this.escapeHtml(learner.status || '');
                
                html += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${learnerName}</td>
                        <td></td>
                        <td>2026</td>
                        <td>${totalStudiedTime}</td>
                        <td>${completedPercentage}%</td>
                        <td>${status}</td>
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
            const paginationContainerTop = document.getElementById('pagination-container-top');
            const paginationListTop = document.getElementById('pagination-list-top');
            
            if (!paginationContainer || !paginationList) return;
            
            if (!pagination.total_pages || pagination.total_pages <= 1) {
                paginationContainer.style.display = 'none';
                if (paginationContainerTop) paginationContainerTop.style.display = 'none';
                return;
            }

            paginationContainer.style.display = 'block';
            if (paginationContainerTop) paginationContainerTop.style.display = 'block';
            
            let html = '';
            const currentPage = pagination.current_page || 1;
            const totalPages = pagination.total_pages;

            // Previous button
            if (currentPage > 1) {
                html += `<li style="display: inline-block; margin: 0 2px;"><a href="#" style="padding: 8px 12px; border: 1px solid #ddd; text-decoration: none;" onclick="window.CMS_TABS.statistics.loadStatisticsData(${currentPage - 1}); return false;">‹</a></li>`;
            }

            // Page numbers
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                const activeClass = i === currentPage ? 'active' : '';
                const bgColor = i === currentPage ? 'background-color: #007bff; color: white;' : '';
                html += `<li style="display: inline-block; margin: 0 2px;" class="${activeClass}"><a href="#" style="padding: 8px 12px; border: 1px solid #ddd; text-decoration: none; ${bgColor}" onclick="window.CMS_TABS.statistics.loadStatisticsData(${i}); return false;">${i}</a></li>`;
            }

            // Next button
            if (currentPage < totalPages) {
                html += `<li style="display: inline-block; margin: 0 2px;"><a href="#" style="padding: 8px 12px; border: 1px solid #ddd; text-decoration: none;" onclick="window.CMS_TABS.statistics.loadStatisticsData(${currentPage + 1}); return false;">›</a></li>`;
            }

            paginationList.innerHTML = html;
            if (paginationListTop) paginationListTop.innerHTML = html;
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

        updateSectionTitles: function() {
            const selectedYear = document.getElementById('filter-year')?.value;
            const displayYear = selectedYear || '2026';
            const titleNodes = document.querySelectorAll('.table-section-title[data-base-title]');

            titleNodes.forEach((node) => {
                const baseTitle = node.getAttribute('data-base-title');
                if (baseTitle) {
                    node.textContent = `${baseTitle} NĂM ${displayYear}`;
                }
            });
        },

        exportStatisticsData: function() {
            // Get current filter parameters
            const filters = {
                phone: (document.getElementById('filter-phone')?.value || '').trim(),
                name: (document.getElementById('filter-name')?.value || '').trim(),
                year: document.getElementById('filter-year')?.value || '',
                completion: document.getElementById('filter-completion')?.value || '',
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

        escapeHtml: function(value) {
            return String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
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

    // Statistics tab module loaded (log removed)
})();