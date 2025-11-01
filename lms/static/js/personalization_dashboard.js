/**
 * Personalization Dashboard JavaScript
 * Handles tab switching, data fetching, and year filtering
 */

(function() {
  'use strict';

  // ==========================================================================
  // Configuration
  // ==========================================================================
  
  const API_BASE_URL = '/personalization/api';
  const ENDPOINTS = {
    userStats: `${API_BASE_URL}/stats/`,
    courseDetails: function(courseId) {
      return `${API_BASE_URL}/course/${encodeURIComponent(courseId)}/`;
    },
    updateLesson: `${API_BASE_URL}/lesson/update/`,
    yearlyStats: `${API_BASE_URL}/yearly-stats/`,
    refreshYearlyStats: `${API_BASE_URL}/yearly-stats/refresh/`,
  };

  // ==========================================================================
  // State Management
  // ==========================================================================
  
  let currentState = {
    activeTab: 'overview',
    selectedYear: new Date().getFullYear(),
    dashboardData: null,
    loading: false
  };

  // ==========================================================================
  // DOM Elements
  // ==========================================================================
  
  const elements = {
    tabs: document.querySelectorAll('.tab-button'),
    tabContents: document.querySelectorAll('.tab-content'),
    yearStartSelect: document.getElementById('year-start'),
    yearEndSelect: document.getElementById('year-end'),
    loadingIndicator: null // Will be created dynamically
  };

  // ==========================================================================
  // Initialization
  // ==========================================================================
  
  function init() {
    console.log('Initializing personalization dashboard...');
    
    // Create loading indicator
    createLoadingIndicator();
    
    // Setup event listeners
    setupTabListeners();
    setupYearSelectorListeners();
    
    // Load initial data
    loadDashboardData();
    
    // Animate progress bars on load
    setTimeout(animateProgressBars, 500);
  }

  // ==========================================================================
  // Tab Management
  // ==========================================================================
  
  function setupTabListeners() {
    elements.tabs.forEach(tab => {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        const targetTab = this.getAttribute('data-tab');
        switchTab(targetTab);
      });
    });
  }

  function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Update state
    currentState.activeTab = tabName;
    
    // Update tab buttons
    elements.tabs.forEach(tab => {
      if (tab.getAttribute('data-tab') === tabName) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });
    
    // Update tab contents
    elements.tabContents.forEach(content => {
      if (content.getAttribute('id') === `${tabName}-tab`) {
        content.classList.add('active');
      } else {
        content.classList.remove('active');
      }
    });
    
    // Load data for specific tabs
    if (tabName === 'detail') {
      loadCourseDetails();
    } else if (tabName === 'assessment') {
      loadAssessmentData();
    }
  }

  // ==========================================================================
  // Year Selector
  // ==========================================================================
  
  function setupYearSelectorListeners() {
    if (elements.yearStartSelect) {
      elements.yearStartSelect.addEventListener('change', handleYearChange);
    }
    
    if (elements.yearEndSelect) {
      elements.yearEndSelect.addEventListener('change', handleYearChange);
    }
  }

  function handleYearChange() {
    const startYear = elements.yearStartSelect ? elements.yearStartSelect.value : currentState.selectedYear;
    const endYear = elements.yearEndSelect ? elements.yearEndSelect.value : currentState.selectedYear;
    
    console.log('Year range changed:', startYear, '-', endYear);
    
    // Update state
    currentState.selectedYear = startYear;
    
    // Reload data with new year filter
    loadDashboardData(startYear, endYear);
  }

  // ==========================================================================
  // Data Loading
  // ==========================================================================
  
  function loadDashboardData(year) {
    console.log('Loading dashboard data for year:', year || 'current');
    
    if (currentState.loading) {
      console.log('Already loading, skipping...');
      return;
    }
    
    showLoading();
    currentState.loading = true;
    
    let url = ENDPOINTS.userStats;
    
    // Add year filter if specified
    if (year) {
      url += `?year=${year}`;
      currentState.selectedYear = year;
    }
    
    fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Dashboard data loaded:', data);
      currentState.dashboardData = data;
      updateDashboardUI(data);
      hideLoading();
      currentState.loading = false;
    })
    .catch(error => {
      console.error('Error loading dashboard data:', error);
      showError('Không thể tải dữ liệu. Vui lòng thử lại sau.');
      hideLoading();
      currentState.loading = false;
    });
  }

  function loadCourseDetails(courseId) {
    console.log('Loading course details for:', courseId);
    
    showLoading();
    
    fetch(ENDPOINTS.courseDetails(courseId), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
      console.log('Course details loaded:', data);
      updateCourseDetailsUI(data);
      hideLoading();
    })
    .catch(error => {
      console.error('Error loading course details:', error);
      showError('Không thể tải chi tiết khóa học.');
      hideLoading();
    });
  }

  function loadAssessmentData() {
    console.log('Assessment feature coming soon...');
    // Placeholder for future emotional assessment integration
  }

  // ==========================================================================
  // UI Updates
  // ==========================================================================
  
  function updateDashboardUI(data) {
    // Update statistics
    updateStatistic('total-courses', data.total_courses || 0);
    updateStatistic('active-courses', data.active_courses || 0);
    updateStatistic('completed-courses', data.completed_courses || 0);
    updateStatistic('total-certificates', data.total_certificates || 0);
    updateStatistic('avg-time', data.avg_time_spent || '0h');
    
    // Update course table
    if (data.course_progress && data.course_progress.length > 0) {
      updateCourseTable(data.course_progress);
    }
    
    // Update sidebar courses
    if (data.active_courses_list) {
      updateActiveCoursesSidebar(data.active_courses_list);
    }
    
    if (data.completed_courses_list) {
      updateCompletedCoursesSidebar(data.completed_courses_list);
    }
    
    // Animate progress bars after update
    setTimeout(animateProgressBars, 300);
  }

  function updateStatistic(id, value) {
    const element = document.getElementById(id);
    if (element) {
      // Animate number change
      animateValue(element, parseInt(element.textContent) || 0, value, 500);
    }
  }

  function updateCourseTable(courses) {
    const tbody = document.querySelector('.course-progress-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    courses.forEach((course, index) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${escapeHtml(course.course_name || 'N/A')}</td>
        <td>${course.completed_lessons || 0}/${course.total_lessons || 0}</td>
        <td><span class="status-badge status-${course.status || 'not_started'}">${getStatusText(course.status)}</span></td>
      `;
      tbody.appendChild(row);
    });
  }

  function updateCourseDetailsUI(courses) {
    const detailList = document.querySelector('.course-detail-list');
    if (!detailList) return;
    
    detailList.innerHTML = '';
    
    if (!courses || courses.length === 0) {
      detailList.innerHTML = '<p class="empty-state">Không có dữ liệu chi tiết</p>';
      return;
    }
    
    courses.forEach(course => {
      const card = document.createElement('div');
      card.className = 'course-detail-card';
      card.innerHTML = `
        <h4>${escapeHtml(course.course_name)}</h4>
        <p>Bài học hoàn thành: ${course.completed_lessons}/${course.total_lessons}</p>
        <p>Thời gian học: ${course.time_spent_hours || 0}h</p>
        <p>Tiến độ: ${course.completion_percentage || 0}%</p>
        <div class="progress-bar-container">
          <div class="progress-bar" data-progress="${course.completion_percentage || 0}"></div>
        </div>
      `;
      detailList.appendChild(card);
    });
    
    // Animate new progress bars
    setTimeout(animateProgressBars, 300);
  }

  function updateActiveCoursesSidebar(courses) {
    const container = document.querySelector('.active-courses-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!courses || courses.length === 0) {
      container.innerHTML = '<p class="empty-state">Chưa có khóa học đang học</p>';
      return;
    }
    
    courses.forEach(course => {
      const card = createCourseCard(course, false);
      container.appendChild(card);
    });
  }

  function updateCompletedCoursesSidebar(courses) {
    const container = document.querySelector('.completed-courses-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!courses || courses.length === 0) {
      container.innerHTML = '<p class="empty-state">Chưa hoàn thành khóa học nào</p>';
      return;
    }
    
    courses.forEach(course => {
      const card = createCourseCard(course, true);
      container.appendChild(card);
    });
  }

  function createCourseCard(course, isCompleted) {
    const card = document.createElement('div');
    card.className = `course-card ${isCompleted ? 'completed' : ''}`;
    
    const progress = isCompleted ? 100 : (course.completion_percentage || 0);
    
    card.innerHTML = `
      <div class="course-icon">
        <img src="/static/images/course-icon.png" alt="Course" onerror="this.src='/static/images/default-course.svg'">
      </div>
      <div class="course-info">
        <p class="course-name" title="${escapeHtml(course.course_name)}">${escapeHtml(course.course_name)}</p>
        <div class="progress-bar-container">
          <div class="progress-bar ${isCompleted ? 'complete' : ''}" data-progress="${progress}"></div>
        </div>
      </div>
    `;
    
    // Add click handler to navigate to course
    card.addEventListener('click', function() {
      window.location.href = `/courses/${course.course_id}/`;
    });
    
    return card;
  }

  // ==========================================================================
  // Animations
  // ==========================================================================
  
  function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
      const progress = bar.getAttribute('data-progress') || 0;
      bar.style.width = '0%';
      
      // Trigger reflow
      bar.offsetWidth;
      
      // Animate to target width
      setTimeout(() => {
        bar.style.width = `${progress}%`;
      }, 50);
    });
  }

  function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        current = end;
        clearInterval(timer);
      }
      
      element.textContent = Math.round(current);
    }, 16);
  }

  // ==========================================================================
  // Loading States
  // ==========================================================================
  
  function createLoadingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'loading-indicator';
    indicator.className = 'loading-indicator';
    indicator.innerHTML = `
      <div class="spinner"></div>
      <p>Đang tải dữ liệu...</p>
    `;
    indicator.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      z-index: 9999;
      display: none;
      text-align: center;
    `;
    
    document.body.appendChild(indicator);
    elements.loadingIndicator = indicator;
  }

  function showLoading() {
    if (elements.loadingIndicator) {
      elements.loadingIndicator.style.display = 'block';
    }
  }

  function hideLoading() {
    if (elements.loadingIndicator) {
      elements.loadingIndicator.style.display = 'none';
    }
  }

  function showError(message) {
    alert(message); // Simple error display, can be enhanced with better UI
  }

  // ==========================================================================
  // Utility Functions
  // ==========================================================================
  
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
  }

  function getStatusText(status) {
    const statusMap = {
      'completed': 'Hoàn thành',
      'in_progress': 'Đang học',
      'not_started': 'Chưa bắt đầu',
      'paused': 'Tạm dừng'
    };
    return statusMap[status] || status;
  }

  // ==========================================================================
  // Auto-refresh (Optional)
  // ==========================================================================
  
  function startAutoRefresh(interval = 300000) { // 5 minutes default
    setInterval(() => {
      if (currentState.activeTab === 'overview') {
        console.log('Auto-refreshing dashboard data...');
        loadDashboardData(currentState.selectedYear, currentState.selectedYear);
      }
    }, interval);
  }

  // ==========================================================================
  // Export Functions for External Use
  // ==========================================================================
  
  window.PersonalizationDashboard = {
    init: init,
    switchTab: switchTab,
    refreshData: loadDashboardData,
    getState: function() { return currentState; }
  };

  // ==========================================================================
  // Auto-initialize when DOM is ready
  // ==========================================================================
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
