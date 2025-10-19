(function () {
  'use strict';

  window.CMS_TABS = window.CMS_TABS || {};
  window.CMS_TABS.management = {
    render: function (container) {
      // Check if user is admin - check is_staff flag or specific roles
      var isAdmin = window.CMS_ROLE_DATA && (
        window.CMS_ROLE_DATA.is_staff || 
        window.CMS_ROLE_DATA.is_global_staff ||
        window.CMS_ROLE_DATA.user_role === 'admin' ||
        window.CMS_ROLE_DATA.user_role === 'bo' ||
        window.CMS_ROLE_DATA.user_role === 'co_quan'
      );
      
      if (!isAdmin) {
        container.innerHTML = '<p>You do not have permission to access this tab.</p>';
        return;
      }

      var apiUrl = '/api/v1/organizations/';

      // HTML for the management interface
      var html = '<div class="organization-management">' +
        '<h2>Quản lý Cơ quan</h2>' +
        '<div class="org-form-container">' +
          '<h3>Tạo cơ quan</h3>' +
          '<form id="org-form" style="margin-bottom: 30px;">' +
            '<div class="form-group" style="margin-bottom: 10px;">' +
              '<label for="org-name">Tên cơ quan:</label>' +
              '<input type="text" id="org-name" placeholder="Nhập tên cơ quan" required style="padding: 8px; width: 300px; max-width: 100%; margin-left: 10px;">' +
            '</div>' +
            '<button type="submit" class="btn btn-primary" style="padding: 8px 16px; background-color: #3494c8; color: white; border: none; border-radius: 4px; cursor: pointer;">Tạo cơ quan</button>' +
            '<span id="form-message" style="margin-left: 10px;"></span>' +
          '</form>' +
        '</div>' +
        '<div class="org-list-container">' +
          '<h3>Danh sách cơ quan</h3>' +
          '<div id="org-list" style="border: 1px solid #ddd; padding: 10px; min-height: 100px;">' +
            '<p>Đang tải...</p>' +
          '</div>' +
        '</div>' +
      '</div>';

      container.innerHTML = html;

      // Get CSRF token from cookies
      function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
      }

      var csrftoken = getCookie('csrftoken');

      // Fetch and display organizations
      function loadOrganizations() {
        fetch(apiUrl, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json'
          }
        })
        .then(function(response) {
          if (!response.ok) {
            throw new Error('Failed to fetch organizations');
          }
          return response.json();
        })
        .then(function(data) {
          var listDiv = document.getElementById('org-list');
          if (Array.isArray(data) && data.length > 0) {
            var html = '<ul style="list-style: none; padding: 0;">';
            data.forEach(function(org) {
              html += '<li style="padding: 8px; border-bottom: 1px solid #eee;">' +
                '<strong>' + (org.name || 'N/A') + '</strong>' +
                ' <span style="color: #999; font-size: 0.9em;">(' + (org.created_at ? new Date(org.created_at).toLocaleDateString() : 'N/A') + ')</span>' +
              '</li>';
            });
            html += '</ul>';
            listDiv.innerHTML = html;
          } else {
            listDiv.innerHTML = '<p style="color: #999;">Chưa có cơ quan nào được tạo.</p>';
          }
        })
        .catch(function(err) {
          console.error('Error loading organizations:', err);
          document.getElementById('org-list').innerHTML = '<p style="color: red;">Lỗi khi tải danh sách cơ quan: ' + err.message + '</p>';
        });
      }

      // Load organizations on page load
      loadOrganizations();

      // Handle form submission
      var form = document.getElementById('org-form');
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        var nameInput = document.getElementById('org-name');
        var orgName = nameInput.value.trim();
        
        if (!orgName) {
          alert('Vui lòng nhập tên cơ quan');
          return;
        }

        var messageSpan = document.getElementById('form-message');
        messageSpan.innerHTML = 'Đang xử lý...';
        messageSpan.style.color = '#999';

        fetch(apiUrl, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: orgName })
        })
        .then(function(response) {
          if (!response.ok) {
            return response.json().then(function(data) {
              throw new Error(data.detail || data.name?.[0] || 'Failed to create organization');
            });
          }
          return response.json();
        })
        .then(function(data) {
          messageSpan.innerHTML = 'Cơ quan đã được tạo thành công!';
          messageSpan.style.color = 'green';
          nameInput.value = '';
          setTimeout(function() { messageSpan.innerHTML = ''; }, 3000);
          loadOrganizations();
        })
        .catch(function(err) {
          console.error('Error creating organization:', err);
          messageSpan.innerHTML = 'Lỗi: ' + err.message;
          messageSpan.style.color = 'red';
        });
      });
    }
  };
})();
