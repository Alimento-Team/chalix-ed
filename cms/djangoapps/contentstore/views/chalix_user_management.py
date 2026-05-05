
# API endpoints added for agency user management (Phase 3)
# These functions handle agency-specific operations like user deletion and bulk import

import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_user_api(request):
    """
    Soft-delete a user by username.
    Agency admins can only delete users within their organization.
    Ministry admins (bo) can delete any user.
    
    Request body:
    {
        "username": "user_to_delete",
        "reason": "optional reason for audit trail"
    }
    """
    from django.contrib.auth.models import User
    from cms.djangoapps.contentstore.models import ChalixUserRole, ChalixOrganization
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        reason = data.get('reason', 'Agency user deletion')
        
        if not username:
            return JsonResponse({'error': _('Username là bắt buộc')}, status=400)
        
        # Get the user to delete
        try:
            user_to_delete = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': _('Người dùng không tồn tại')}, status=404)
        
        # Check requester's role and permissions
        requester_roles = ChalixUserRole.objects.filter(user=request.user, is_active=True)
        
        # Ministry admin (bo) can delete anyone
        is_ministry_admin = requester_roles.filter(role='bo').exists()
        
        # Agency admin (co_quan) can only delete users in their org
        if not is_ministry_admin:
            requester_org_ids = requester_roles.filter(role='co_quan').values_list('organization_id', flat=True)
            if not requester_org_ids:
                return JsonResponse({'error': _('Không có quyền xóa người dùng')}, status=403)
            
            # Check if user to delete is in same organization
            target_user_orgs = ChalixUserRole.objects.filter(
                user=user_to_delete, is_active=True
            ).values_list('organization_id', flat=True)
            
            if not any(org_id in requester_org_ids for org_id in target_user_orgs):
                return JsonResponse({'error': _('Không có quyền xóa người dùng này')}, status=403)
        
        # Perform soft delete
        user_to_delete.is_active = False
        user_to_delete.save(update_fields=['is_active'])
        
        # Soft-delete associated roles
        ChalixUserRole.objects.filter(user=user_to_delete).update(is_active=False)
        
        logger.info(
            f"User {user_to_delete.username} soft-deleted by {request.user.username}. Reason: {reason}"
        )
        
        return JsonResponse({
            'success': True,
            'message': _('Xóa người dùng thành công'),
            'username': username,
            'deleted_at': user_to_delete.last_login  # For audit trail context
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': _('Dữ liệu JSON không hợp lệ')}, status=400)
    except PermissionDenied:
        return JsonResponse({'error': _('Không có quyền')}, status=403)
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ')}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def import_users_api(request):
    """
    Bulk import users from Excel file.
    Agency admins can only import to their organization.
    Ministry admins (bo) can import to any organization.
    
    Form data:
    - file: Excel file with user data
    - organization_id: target organization ID
    """
    from django.contrib.auth.models import User
    from cms.djangoapps.contentstore.models import ChalixUserRole, ChalixOrganization
    from cms.djangoapps.contentstore.utils.excel_import import import_users_from_excel
    
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': _('File Excel là bắt buộc')}, status=400)
        
        organization_id = request.POST.get('organization_id')
        if not organization_id:
            return JsonResponse({'error': _('Organization ID là bắt buộc')}, status=400)
        
        # Get organization
        try:
            organization = ChalixOrganization.objects.get(id=organization_id)
        except ChalixOrganization.DoesNotExist:
            return JsonResponse({'error': _('Tổ chức không tồn tại')}, status=404)
        
        # Check requester's permission to import to this organization
        requester_roles = ChalixUserRole.objects.filter(user=request.user, is_active=True)
        
        # Ministry admin (bo) can import to any org
        is_ministry_admin = requester_roles.filter(role='bo').exists()
        
        if not is_ministry_admin:
            # Agency admin can only import to their own org
            has_access = requester_roles.filter(
                role='co_quan', organization=organization
            ).exists()
            
            if not has_access:
                return JsonResponse({
                    'error': _('Không có quyền nhập người dùng vào tổ chức này')
                }, status=403)
        
        # Process Excel import
        excel_file = request.FILES['file']
        result = import_users_from_excel(excel_file, organization)
        
        logger.info(
            f"Imported {result.get('created_count', 0)} users to {organization.name} "
            f"by {request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': _('Nhập người dùng thành công'),
            'created_count': result.get('created_count', 0),
            'failed_count': result.get('failed_count', 0),
            'errors': result.get('errors', [])
        })
        
    except PermissionDenied:
        return JsonResponse({'error': _('Không có quyền')}, status=403)
    except Exception as e:
        logger.error(f"Error importing users: {str(e)}", exc_info=True)
        return JsonResponse({'error': _('Lỗi hệ thống nội bộ'), 'detail': str(e)}, status=500)
