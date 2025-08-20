# Teacher Dashboard for edX Platform

This module provides a teacher dashboard feature for the edX platform, allowing instructors and course staff to view all courses they are teaching in a unified interface.

## Features

- **Course Overview**: Shows all courses where the user has instructor or staff permissions
- **Vietnamese Localization**: Interface designed in Vietnamese as per the Figma specification
- **Role-based Access**: Only users with instructor or staff roles can access the dashboard
- **Responsive Design**: Mobile-friendly interface with responsive tabs
- **Course Navigation**: Direct links to course instructor dashboards for detailed management

## Files Created

### Backend (Django)
- `lms/djangoapps/teacher_dashboard/` - Main Django app
  - `apps.py` - Django app configuration
  - `views.py` - Main view logic for the teacher dashboard
  - `utils.py` - Utility functions for fetching instructor courses
  - `urls.py` - URL routing configuration
  - `tests.py` - Unit tests for the functionality

### Frontend (Templates)
- `lms/templates/teacher_dashboard/teacher_dashboard.html` - Main template that matches the Figma design

### Integration
- Updated `lms/urls.py` - Added teacher dashboard URL routing
- Updated `lms/envs/common.py` - Added teacher dashboard to INSTALLED_APPS
- Updated `lms/templates/header/chalix-header.html` - Added "Giảng Dạy" button for instructors

## URL Structure

- `/teacher-dashboard/` - Main teacher dashboard page

## User Interface

The dashboard includes four tabs:
1. **Lớp học đang giảng dạy** (Current Teaching Classes) - Active tab showing course list
2. **Lịch giảng dạy** (Teaching Schedule) - Placeholder for future development
3. **Lịch kiểm tra** (Test Schedule) - Placeholder for future development
4. **Đánh giá kết quả** (Grade Assessment) - Placeholder for future development

## Access Control

- Users must be authenticated to access the dashboard
- Users must have either `CourseInstructorRole` or `CourseStaffRole` for at least one course
- The dashboard automatically shows only courses where the user has teaching permissions

## Course Data

The dashboard displays:
- Course name
- Course schedule (start/end dates)
- Edit and menu actions for each course

## Header Integration

For users with instructor or staff roles, a "Giảng Dạy" (Teaching) button appears in the header next to the "Học Tập" (Learning) button, providing quick access to the teacher dashboard.

## Testing

Run the included test script:
```bash
python test_teacher_dashboard.py
```

Or run the Django tests:
```bash
python manage.py test lms.djangoapps.teacher_dashboard
```

## Design Reference

The interface is based on the provided Figma design with Vietnamese text and follows the existing edX platform styling conventions while implementing the specific visual requirements from the design mockup.

## Future Enhancements

The current implementation provides the foundation for:
- Teaching schedule management
- Test scheduling
- Grade assessment tools
- Course analytics for instructors
- Bulk course operations

## Dependencies

This feature relies on existing edX platform components:
- Student roles system (`common.djangoapps.student.roles`)
- Course overview models (`openedx.core.djangoapps.content.course_overviews`)
- Course access controls (`lms.djangoapps.courseware.access`)
- Existing instructor dashboard for individual course management
