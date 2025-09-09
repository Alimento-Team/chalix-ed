# Chalix User Menu System

## Overview

This system implements a comprehensive user account dropdown menu for the Chalix educational platform, based on the Figma design specifications. It provides Vietnamese language support and includes both frontend and backend components.

## Features

The user menu includes the following Vietnamese menu items with corresponding backend functionality:

1. **Khóa học** (Courses) - View and manage enrolled courses
2. **Cập nhật thông tin** (Update Information) - Update user profile information
3. **Cá nhân hóa** (Personalization) - Customize learning preferences and settings
4. **Danh sách yêu cầu** (Request List) - View and manage user requests
5. **Kết quả học tập** (Learning Results) - View learning progress and achievements
6. **Lập kế hoạch cá nhân** (Personal Learning Plan) - Create and manage learning plans
7. **Đăng ký giảng dạy** (Teaching Registration) - Register to become an instructor
8. **Trợ giúp** (Help) - Access help resources and support
9. **Đăng xuất** (Logout) - Logout from the system

## Frontend Implementation

### Header Component (`ChalixHeader.jsx`)

The header component includes:
- User avatar with clickable dropdown functionality
- Responsive design matching the Figma specifications
- Vietnamese language labels
- Click outside to close dropdown functionality
- Keyboard accessibility support

### Styling (`ChalixHeader.scss`)

- Matches Figma design specifications exactly
- Uses Roboto font family as specified
- Proper color scheme (#3494c8, #99abc8, etc.)
- Responsive design for mobile and desktop
- Dropdown menu with shadow and proper positioning

### Menu Items Configuration

Each menu item includes:
- Vietnamese label
- Icon (optional)
- Action handler for navigation/API calls

## Backend Implementation

### Django App: `chalix_user_menu`

Located at: `lms/djangoapps/chalix_user_menu/`

### Models

1. **UserLearningPlan**
   - Stores user's personal learning plans
   - Fields: title, description, target_hours, completed_hours, start_date, end_date, status
   - Includes progress calculation

2. **TeachingRequest**
   - Manages teaching registration requests
   - Fields: course_title, course_description, teaching_experience, qualifications, status
   - Includes approval workflow

3. **UserRequest**
   - General user request management
   - Fields: request_type, title, description, status, priority
   - Support for different request categories

4. **UserPersonalization**
   - User preference storage
   - Fields: learning_style, preferred_language, notification_preferences, theme_preference
   - JSON fields for flexible preference storage

### API Endpoints

Base URL: `/api/chalix/user-menu/`

1. `GET /courses/` - Get user's enrolled courses with progress
2. `GET|POST /personalization/` - Get/update personalization settings
3. `GET|POST /requests/` - Get user requests or create new request
4. `GET /learning-results/` - Get learning progress and achievements
5. `GET|POST /learning-plans/` - Get/create learning plans
6. `GET|POST /teaching/` - Get teaching requests or register for teaching
7. `GET /help/` - Get help resources
8. `POST /logout/` - Logout user

### Admin Interface

- Full admin support for all models
- Vietnamese field labels
- Proper filtering and searching
- Workflow management for approvals

## Setup Instructions

### 1. Backend Setup

1. Add the app to `INSTALLED_APPS` in settings:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'lms.djangoapps.chalix_user_menu',
]
```

2. Run migrations:
```bash
python manage.py makemigrations chalix_user_menu
python manage.py migrate
```

3. The URLs are already included in `lms/urls.py`

### 2. Frontend Setup

The header component is already updated with the dropdown menu functionality. No additional setup required.

### 3. Configuration

Update the following configuration variables if needed:
- `LMS_BASE_URL` - Base URL for the LMS
- `ACCOUNT_PROFILE_URL` - URL for user profile pages

## API Usage Examples

### Get User Courses
```javascript
fetch('/api/chalix/user-menu/courses/', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    }
})
.then(response => response.json())
.then(data => console.log(data.courses));
```

### Create Learning Plan
```javascript
fetch('/api/chalix/user-menu/learning-plans/', {
    method: 'POST',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        title: 'My Learning Plan',
        description: 'Personal learning goals for 2025',
        target_hours: 100,
        start_date: '2025-01-01',
        end_date: '2025-12-31'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Submit User Request
```javascript
fetch('/api/chalix/user-menu/requests/', {
    method: 'POST',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        request_type: 'technical_support',
        title: 'Cannot access course videos',
        description: 'I am unable to play videos in Course XYZ',
        priority: 'medium'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Testing

### Frontend Testing

Test the dropdown menu functionality:
1. Click on user avatar to open dropdown
2. Verify all menu items are displayed with correct Vietnamese labels
3. Test click outside to close functionality
4. Test keyboard navigation (Tab, Enter)
5. Verify responsive behavior on mobile

### Backend Testing

Test API endpoints:
1. Verify authentication requirements
2. Test CRUD operations for each model
3. Test data validation and error handling
4. Verify Vietnamese language support in responses

## Security Considerations

- All API endpoints require user authentication
- CSRF protection is enabled
- Input validation on all user data
- Proper permission checks for sensitive operations

## Internationalization

- All user-facing text is in Vietnamese
- Uses Django's translation framework for future language support
- Proper Unicode handling for Vietnamese characters

## Future Enhancements

1. Real-time notifications for request status updates
2. Advanced filtering and search for user data
3. Integration with external learning analytics tools
4. Mobile app API support
5. Advanced personalization algorithms based on learning patterns

## Troubleshooting

### Common Issues

1. **Dropdown not appearing**: Check CSS z-index values and positioning
2. **API 403 errors**: Verify user authentication and CSRF tokens
3. **Vietnamese text not displaying**: Check Unicode encoding and font support
4. **Migration errors**: Ensure all dependencies are installed

### Debugging

Enable debug logging in settings:
```python
LOGGING = {
    'loggers': {
        'lms.djangoapps.chalix_user_menu': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Support

For technical support or questions:
- Email: dev@chalix.edu.vn
- Internal documentation: `/docs/chalix-user-menu/`
