"""
Template generator for bulk user creation Excel file.
Users can download this template to understand the format required.
"""

import csv
import io
import os
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([BearerAuthenticationAllowInactiveUser])
@permission_classes([ApiKeyHeaderPermissionIsAuthenticated])
def download_user_template(request):
    """
    Download Excel template for bulk user creation
    """
    try:
        # Create CSV template (can be opened in Excel)
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers in Vietnamese
        headers = [
            'ho_ten',          # Full Name  
            'email',           # Email
            'mat_khau',        # Password
            'vai_tro',         # Role (bo, co_quan, giang_vien, cong_chuc)
            'trang_thai',      # Status (hoat_dong, khong_hoat_dong)
            'ghi_chu'          # Notes (optional)
        ]
        
        writer.writerow(headers)
        
        # Add sample data rows
        sample_rows = [
            [
                'Nguyễn Văn A',
                'nguyenvana@example.com', 
                'password123',
                'giang_vien',
                'hoat_dong',
                'Giảng viên khoa Toán'
            ],
            [
                'Trần Thị B',
                'tranthib@example.com',
                'password456', 
                'cong_chuc',
                'hoat_dong',
                'Công chức phòng Đào tạo'
            ],
            [
                'Lê Minh C',
                'leminhc@example.com',
                'password789',
                'co_quan',
                'khong_hoat_dong',
                'Đại diện cơ quan X'
            ]
        ]
        
        for row in sample_rows:
            writer.writerow(row)
        
        # Add instructions at the end
        writer.writerow([])
        writer.writerow(['=== HƯỚNG DẪN SỬ DỤNG ==='])
        writer.writerow(['1. Điền đầy đủ thông tin vào các cột bắt buộc'])
        writer.writerow(['2. Vai trò (vai_tro): bo, co_quan, giang_vien, cong_chuc'])
        writer.writerow(['3. Trạng thái (trang_thai): hoat_dong, khong_hoat_dong']) 
        writer.writerow(['4. Email phải là duy nhất trong hệ thống'])
        writer.writerow(['5. Mật khẩu phải có ít nhất 6 ký tự'])
        writer.writerow(['6. Xóa các dòng mẫu này trước khi tải lên'])
        
        # Create response
        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="chalix_user_template.csv"'
        
        return response
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Lỗi tạo file mẫu: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([BearerAuthenticationAllowInactiveUser]) 
@permission_classes([ApiKeyHeaderPermissionIsAuthenticated])
def get_upload_instructions(request):
    """
    Get instructions for bulk upload format
    """
    instructions = {
        'success': True,
        'format_description': {
            'supported_formats': ['.csv', '.xlsx', '.xls'],
            'required_columns': [
                {
                    'name': 'ho_ten',
                    'description': 'Họ và tên đầy đủ',
                    'required': True,
                    'example': 'Nguyễn Văn A'
                },
                {
                    'name': 'email', 
                    'description': 'Địa chỉ email (phải duy nhất)',
                    'required': True,
                    'example': 'nguyenvana@example.com'
                },
                {
                    'name': 'mat_khau',
                    'description': 'Mật khẩu (ít nhất 6 ký tự)',
                    'required': True,
                    'example': 'password123'
                },
                {
                    'name': 'vai_tro',
                    'description': 'Vai trò người dùng',
                    'required': True,
                    'options': ['bo', 'co_quan', 'giang_vien', 'cong_chuc'],
                    'example': 'giang_vien'
                },
                {
                    'name': 'trang_thai',
                    'description': 'Trạng thái tài khoản',
                    'required': True,
                    'options': ['hoat_dong', 'khong_hoat_dong'],
                    'example': 'hoat_dong'
                },
                {
                    'name': 'ghi_chu',
                    'description': 'Ghi chú (tùy chọn)',
                    'required': False,
                    'example': 'Giảng viên khoa Toán'
                }
            ],
            'notes': [
                'File có thể chứa tối đa 1000 người dùng',
                'Email phải là duy nhất trong hệ thống',
                'Vai trò được tạo phụ thuộc vào quyền của người tạo',
                'Mật khẩu sẽ được tự động mã hóa',
                'Các dòng có lỗi sẽ được báo cáo chi tiết'
            ]
        }
    }
    
    return Response(instructions)