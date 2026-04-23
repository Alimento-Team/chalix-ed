"""
Views for user management in the Chalix CMS interface.
"""
import logging
import json
import csv
import io
from typing import Optional, List, Dict, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.lib.api.view_utils import view_auth_classes
from common.djangoapps.student.helpers import do_create_account, AccountValidationError
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from ..models import ChalixUserRole, ChalixOrganization
from cms.djangoapps.contentstore.chalix_roles import (
    is_bo_user,
    is_co_quan_user,
    is_giang_vien_user,
    is_cong_chuc_user,
    get_user_primary_role
)

log = logging.getLogger(__name__)
User = get_user_model()


@view_auth_classes(is_authenticated=True)
@api_view(['POST'])
def create_user_account(request):
    """
    Create a new user account with Chalix role assignment.
    
    Expected data:
    {
        "full_name": "Nguyen Van A",
        "email": "user@example.com", 
        "password": "secure_password",
        "role": "giang_vien",
        "organization_id": 1,
        "status": "active"
    }
    """
    try:
        # Check if current user has permission to create accounts
        current_user_role = get_user_current_role(request.user)
        if not can_create_user_accounts(current_user_role):
            return Response({
                'success': False,
                'message': _('Bạn không có quyền tạo tài khoản người dùng.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input data
        data = request.data
        required_fields = ['full_name', 'email', 'password', 'status']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return Response({
                'success': False,
                'message': _('Thiếu thông tin bắt buộc: {}').format(', '.join(missing_fields))
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate role assignment permissions - default to cong_chuc if not provided
        target_role = data.get('role', 'cong_chuc')
        # Accept both 'organization' and 'organization_id' field names
        target_org_id = data.get('organization') or data.get('organization_id')
        
        # Extract role string from current_user_role object
        current_role_str = current_user_role.role if current_user_role else None
        
        if not can_assign_role(current_role_str, target_role):
            return Response({
                'success': False,
                'message': _('Bạn không có quyền gán vai trò này.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # For co_quan users (org admins), automatically assign their organization
        if current_role_str == 'co_quan':
            current_org = getattr(current_user_role, 'organization', None)
            if not current_org:
                return Response({
                    'success': False,
                    'message': _('Không thể xác định tổ chức của bạn.')
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Org admins can only create users in their own organization
            # Always use admin's org, ignore any org specified in the request
            target_org_id = current_org.id
        
        # Validate email
        email = data.get('email').strip()
        try:
            validate_email(email)
        except ValidationError:
            return Response({
                'success': False,
                'message': _('Email không hợp lệ.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': _('Email đã được sử dụng.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique username from email
        username = generate_unique_username(email)
        
        # Get organization
        organization = None
        if target_org_id:
            try:
                organization = ChalixOrganization.objects.get(
                    id=target_org_id, 
                    is_active=True
                )
            except ChalixOrganization.DoesNotExist:
                return Response({
                    'success': False,
                    'message': _('Tổ chức không tồn tại.')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user account
        with transaction.atomic():
            user_data = {
                'email': email,
                'username': username,
                'password': data['password'],
                'name': data['full_name'],
            }
            
            form_data = {
                'email': email,
                'username': username,
                'password': data['password'],
                'name': data['full_name'],
            }
            
            account_creation_form = AccountCreationForm(
                data=form_data,
                tos_required=False
            )
            
            try:
                user, profile, registration = do_create_account(account_creation_form)
            except (ValidationError, AccountValidationError) as e:
                return Response({
                    'success': False,
                    'message': _('Lỗi tạo tài khoản: {}').format(str(e))
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Activate user if status is active
            if data.get('status') == 'active':
                user.is_active = True
                user.save()
            
            # Create Chalix user role
            chalix_role = ChalixUserRole.objects.create(
                user=user,
                role=target_role,
                organization=organization,
                is_active=(data.get('status') == 'active'),
                created_by=request.user
            )
            
            log.info(
                f"User account created successfully: {email} with role {target_role} by {request.user.email}"
            )
            
            return Response({
                'success': True,
                'message': _('Tạo tài khoản thành công.'),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': profile.name,
                    'role': chalix_role.get_role_display(),
                    'organization': organization.display_name if organization else None,
                    'is_active': chalix_role.is_active
                }
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        log.error(f"Error creating user account: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': _('Lỗi hệ thống. Vui lòng thử lại sau.')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
@api_view(['POST'])
def bulk_create_users(request):
    """
    Create multiple user accounts from uploaded Excel file.
    """
    try:
        # Check permissions
        current_user_role = get_user_current_role(request.user)
        if not can_create_user_accounts(current_user_role):
            return Response({
                'success': False,
                'message': _('Bạn không có quyền tạo tài khoản người dùng.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': _('Vui lòng tải lên file Excel.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        if not uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            return Response({
                'success': False,
                'message': _('File phải có định dạng Excel (.xlsx, .xls) hoặc CSV.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse file
        try:
            users_data = parse_users_file(uploaded_file)
        except Exception as e:
            return Response({
                'success': False,
                'message': _('Lỗi đọc file: {}').format(str(e))
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not users_data:
            return Response({
                'success': False,
                'message': _('File không chứa dữ liệu hợp lệ.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate users data
        validated_users = []
        validation_errors = []
        
        for row_num, user_data in enumerate(users_data, 1):
            try:
                # Validate required fields
                required_fields = ['full_name', 'email']
                missing = [f for f in required_fields if not user_data.get(f)]
                if missing:
                    validation_errors.append(f"Dòng {row_num}: Thiếu thông tin {', '.join(missing)}")
                    continue
                
                # Set default role to cong_chuc if not provided
                if not user_data.get('role'):
                    user_data['role'] = 'cong_chuc'
                
                # Validate email
                try:
                    validate_email(user_data['email'])
                except ValidationError:
                    validation_errors.append(f"Dòng {row_num}: Email không hợp lệ")
                    continue
                
                # Validate role permissions
                current_role_str = current_user_role.role if current_user_role else None
                if not can_assign_role(current_role_str, user_data['role']):
                    validation_errors.append(f"Dòng {row_num}: Không có quyền gán vai trò {user_data['role']}")
                    continue
                
                # Check if user already exists
                if User.objects.filter(email=user_data['email']).exists():
                    validation_errors.append(f"Dòng {row_num}: Email {user_data['email']} đã tồn tại")
                    continue
                
                # Generate password if not provided
                if not user_data.get('password'):
                    user_data['password'] = generate_random_password()
                
                validated_users.append(user_data)
                
            except Exception as e:
                validation_errors.append(f"Dòng {row_num}: Lỗi xử lý - {str(e)}")
        
        if validation_errors:
            return Response({
                'success': False,
                'message': _('File có lỗi:'),
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create users
        created_users = []
        creation_errors = []
        
        for user_data in validated_users:
            try:
                with transaction.atomic():
                    username = generate_unique_username(user_data['email'])
                    
                    form_data = {
                        'email': user_data['email'],
                        'username': username,
                        'password': user_data['password'],
                        'name': user_data['full_name'],
                    }
                    
                    account_creation_form = AccountCreationForm(
                        data=form_data,
                        tos_required=False
                    )
                    
                    user, profile, registration = do_create_account(account_creation_form)
                    
                    # Activate user by default
                    user.is_active = True
                    user.save()
                    
                    # Get organization if specified
                    organization = None
                    if user_data.get('organization_id'):
                        organization = ChalixOrganization.objects.get(
                            id=user_data['organization_id'],
                            is_active=True
                        )
                    
                    # Create Chalix role
                    ChalixUserRole.objects.create(
                        user=user,
                        role=user_data['role'],
                        organization=organization,
                        is_active=True,
                        created_by=request.user
                    )
                    
                    created_users.append({
                        'email': user.email,
                        'full_name': profile.name,
                        'role': user_data['role'],
                        'password': user_data['password']  # Include for admin to share with user
                    })
                    
            except Exception as e:
                creation_errors.append(f"Lỗi tạo tài khoản {user_data['email']}: {str(e)}")
        
        log.info(
            f"Bulk user creation completed by {request.user.email}: "
            f"{len(created_users)} successful, {len(creation_errors)} errors"
        )
        
        return Response({
            'success': True,
            'message': _('Hoàn thành tạo tài khoản hàng loạt.'),
            'created_count': len(created_users),
            'error_count': len(creation_errors),
            'created_users': created_users,
            'errors': creation_errors if creation_errors else None
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        log.error(f"Error in bulk user creation: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': _('Lỗi hệ thống. Vui lòng thử lại sau.')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
@api_view(['GET'])
def get_user_organizations(request):
    """
    Get list of organizations that current user can assign to new users.
    """
    try:
        current_user_role = get_user_current_role(request.user)
        
        if not current_user_role:
            return Response({
                'success': False,
                'message': _('Không tìm thấy thông tin vai trò của bạn.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Filter organizations based on user role
        organizations = ChalixOrganization.objects.filter(is_active=True)
        
        # For bo role, can see all organizations
        # For co_quan role, can only see their own organization
        if is_co_quan_user(request.user):
            user_org = current_user_role.organization
            if user_org:
                # Co quan admin can only see their own organization
                organizations = organizations.filter(id=user_org.id)
            else:
                organizations = organizations.none()
        elif not is_bo_user(request.user):
            # Other roles cannot create users
            organizations = organizations.none()
        
        org_data = [{
            'id': org.id,
            'name': org.name,
            'value': org.id,
            'label': org.display_name if hasattr(org, 'display_name') and org.display_name else org.name,
            'display_name': org.display_name if hasattr(org, 'display_name') and org.display_name else org.name
        } for org in organizations.order_by('name')]
        
        return Response({
            'success': True,
            'organizations': org_data
        })
        
    except Exception as e:
        log.error(f"Error getting user organizations: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': _('Lỗi hệ thống. Vui lòng thử lại sau.')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@view_auth_classes(is_authenticated=True)
@api_view(['GET'])
def get_available_roles(request):
    """
    Get list of roles that current user can assign to new users.
    """
    try:
        current_user_role = get_user_current_role(request.user)
        
        if not current_user_role:
            return Response({
                'success': False,
                'message': _('Không tìm thấy thông tin vai trò của bạn.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        available_roles = get_assignable_roles(current_user_role.role)
        
        role_data = [{
            'value': role_value,
            'display_name': role_display
        } for role_value, role_display in available_roles]
        
        return Response({
            'success': True,
            'roles': role_data
        })
        
    except Exception as e:
        log.error(f"Error getting available roles: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': _('Lỗi hệ thống. Vui lòng thử lại sau.')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_user_current_role(user) -> Optional[ChalixUserRole]:
    """Get the current active Chalix role for a user."""
    try:
        role = ChalixUserRole.objects.filter(
            user=user,
            is_active=True
        ).first()

        if role:
            return role

        # If the user is a Django staff or superuser, provide a lightweight
        # fallback role so admin accounts can use the management endpoints.
        # We treat staff/superuser as 'bo' (ministry-level) for permission checks.
        try:
            from types import SimpleNamespace
            if user and (getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)):
                return SimpleNamespace(role='bo', organization=None)
        except Exception:
            # If anything goes wrong constructing the fallback, just return None
            return None

        return None
    except Exception:
        return None


@view_auth_classes(is_authenticated=True)
@api_view(['GET'])
def list_users(request):
    """
    Return a paginated list of users visible to the current requester.

    Query params:
      - page (int, default=1)
      - per_page (int, default=50)

        Response shape:
            {
                'success': True,
                'users': [ { id, username, name, gender, email, department, system_user_role }, ... ],
                'total': <int>,
                'page': <int>,
                'per_page': <int>
            }
    """
    try:
        current_role = get_user_current_role(request.user)
        if not current_role:
            return Response({
                'success': False,
                'message': _('Không tìm thấy thông tin vai trò của bạn.')
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            page = int(request.GET.get('page', 1))
        except Exception:
            page = 1

        try:
            per_page = int(request.GET.get('per_page', 50))
        except Exception:
            per_page = 50

        # Base queryset
        users_qs = User.objects.select_related('profile').all().order_by('id')

        # Optional search filter
        q = request.GET.get('q', '').strip()
        if q:
            # filter username, email, or profile name (if available)
            from django.db.models import Q
            users_qs = users_qs.filter(
                Q(username__icontains=q) | Q(email__icontains=q) | Q(profile__name__icontains=q)
            )

        # Restrict visible users based on current role
        if is_co_quan_user(request.user):
            user_org = getattr(current_role, 'organization', None)
            if user_org:
                org_ids = [user_org.id]
                try:
                    org_ids.extend(list(user_org.children.values_list('id', flat=True)))
                except Exception:
                    pass
                role_qs = ChalixUserRole.objects.filter(organization__id__in=org_ids, is_active=True)
                user_ids = role_qs.values_list('user_id', flat=True)
                users_qs = users_qs.filter(id__in=user_ids)
            else:
                users_qs = users_qs.none()
        elif is_bo_user(request.user):
            # bo can see all users
            pass
        else:
            # other roles not permitted to list accounts
            users_qs = users_qs.none()

        total = users_qs.count()

        # Simple pagination
        start = (page - 1) * per_page
        end = start + per_page
        users_page = list(users_qs[start:end])

        # Prefetch roles for the selected users to avoid N+1
        role_objs = ChalixUserRole.objects.filter(user__in=users_page, is_active=True).select_related('organization')
        role_map = {r.user_id: r for r in role_objs}

        users_data = []
        for u in users_page:
            profile = getattr(u, 'profile', None)
            full_name = None
            if profile and getattr(profile, 'name', None):
                full_name = profile.name
            else:
                full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username or u.email

            phone = None
            if profile and getattr(profile, 'phone_number', None):
                phone = profile.phone_number

            r = role_map.get(u.id)
            org_display = None
            role_display = None
            if r:
                org_display = r.organization.display_name if r.organization else None
                try:
                    role_display = r.get_role_display()
                except Exception:
                    role_display = getattr(r, 'role', None)
            
            # Get meta data from profile
            meta_data = {}
            gender_display = None
            if profile:
                try:
                    meta_data = profile.get_meta() if hasattr(profile, 'get_meta') else {}
                except Exception:
                    meta_data = {}
                
                # Get gender display
                if profile.gender:
                    gender_display = profile.gender

            users_data.append({
                'id': u.id,
                'username': u.username,
                'name': full_name,
                'full_name': full_name,
                'phone': phone,
                'email': u.email,
                'department': org_display,
                'organization': org_display,
                'role': role_display,
                'gender': gender_display,
                'system_user_role': 'Tài khoản Công chức/Viên chức',
                'meta': meta_data,
                'user_role': 'Tài khoản Công chức/Viên chức'
            })

        return Response({
            'success': True,
            'users': users_data,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        log.error(f"Error listing users: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': _('Lỗi hệ thống. Vui lòng thử lại sau.')
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def can_create_user_accounts(current_role: Optional[ChalixUserRole]) -> bool:
    """Check if current user role allows creating new accounts."""
    if not current_role:
        return False
    
    # Only bo and co_quan roles can create accounts
    return current_role.role in ['bo', 'co_quan']


def can_assign_role(current_role_value: str, target_role: str) -> bool:
    """Check if current role can assign the target role."""
    if not current_role_value:
        return False
    
    if current_role_value == 'bo':
        # Ministry level can assign all roles except bo itself
        return target_role in ['co_quan', 'giang_vien', 'cong_chuc']
    elif current_role_value == 'co_quan':
        # Organization level can assign teacher and learner roles within their org
        return target_role in ['giang_vien', 'cong_chuc']
    
    # Other roles (giang_vien, cong_chuc) cannot assign roles
    return False


def get_assignable_roles(current_role: str) -> List[tuple]:
    """Get list of roles that current role can assign."""
    role_choices = ChalixUserRole.ROLE_CHOICES
    
    if current_role == 'bo':
        # Ministry can assign all roles including bo itself
        return role_choices
    elif current_role == 'co_quan':
        # Organization can assign: giang_vien, cong_chuc
        return [choice for choice in role_choices if choice[0] in ['giang_vien', 'cong_chuc']]
    
    return []


def generate_unique_username(email: str) -> str:
    """Generate a unique username from email."""
    base_username = email.split('@')[0]
    
    # Remove non-alphanumeric characters
    import re
    base_username = re.sub(r'[^a-zA-Z0-9]', '', base_username)
    
    if not base_username:
        base_username = 'user'
    
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


def generate_random_password(length: int = 8) -> str:
    """Generate a random password."""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return password


def parse_users_file(uploaded_file) -> List[Dict[str, Any]]:
    """Parse uploaded Excel or CSV file containing user data."""
    users_data = []
    
    if uploaded_file.name.endswith('.csv'):
        # Parse CSV file
        file_content = uploaded_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        for row in csv_reader:
            users_data.append({
                'full_name': row.get('ho_va_ten', '').strip(),
                'email': row.get('email', '').strip(),
                'password': row.get('mat_khau', '').strip(),
                'role': row.get('vai_tro', '').strip(),
                'organization_id': row.get('ma_to_chuc', '').strip() or None,
                'status': row.get('trang_thai', 'active').strip()
            })
    
    else:
        # Parse Excel file
        try:
            import pandas as pd
            
            df = pd.read_excel(uploaded_file)
            
            for index, row in df.iterrows():
                users_data.append({
                    'full_name': str(row.get('ho_va_ten', '')).strip(),
                    'email': str(row.get('email', '')).strip(),
                    'password': str(row.get('mat_khau', '')).strip(),
                    'role': str(row.get('vai_tro', '')).strip(),
                    'organization_id': row.get('ma_to_chuc') if pd.notna(row.get('ma_to_chuc')) else None,
                    'status': str(row.get('trang_thai', 'active')).strip()
                })
                
        except ImportError:
            raise Exception(_('Hệ thống không hỗ trợ đọc file Excel. Vui lòng sử dụng file CSV.'))
    
    return users_data


@view_auth_classes(is_authenticated=True)
@api_view(['GET'])
def get_user_detail(request, user_id):
    """
    Get details of a specific user.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Check permission - only Bo or admin of same organization
        current_user_role = get_user_current_role(request.user)
        if not current_user_role:
            return Response(
                {'error': 'Bạn không có quyền xem thông tin người dùng'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Bo can see all users
        if is_bo_user(request.user):
            pass
        # Admin can only see users in their organization
        elif is_co_quan_user(request.user):
            user_role = get_user_current_role(user)
            if not user_role or user_role.organization != current_user_role.organization:
                return Response(
                    {'error': 'Bạn không có quyền xem thông tin người dùng này'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Bạn không có quyền xem thông tin người dùng'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user role and organization
        user_role = get_user_current_role(user)
        
        # Get user profile meta
        from common.djangoapps.student.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
            # Handle meta field - it might be a string (JSON) or dict
            if hasattr(profile, 'meta') and profile.meta:
                if isinstance(profile.meta, str):
                    try:
                        meta = json.loads(profile.meta)
                    except (json.JSONDecodeError, ValueError):
                        meta = {}
                elif isinstance(profile.meta, dict):
                    meta = profile.meta
                else:
                    meta = {}
            else:
                meta = {}
            full_name = profile.name if hasattr(profile, 'name') and profile.name else ''
        except UserProfile.DoesNotExist:
            meta = {}
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or user.email
        
        if not full_name:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or user.email
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': full_name,
            'phone': meta.get('phone', ''),
            'gender': meta.get('gender', ''),
            'organization': user_role.organization.name if user_role and user_role.organization else '',
            'organization_id': user_role.organization.id if user_role and user_role.organization else None,
            'user_role': user_role.role if user_role else '',
            'meta': meta
        }
        
        return Response(user_data)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Không tìm thấy người dùng'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        log.error(f'Error getting user detail: {str(e)}')
        return Response(
            {'error': f'Lỗi khi lấy thông tin người dùng: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@view_auth_classes(is_authenticated=True)
@api_view(['PATCH'])
def update_user(request, user_id):
    """
    Update user information.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Check permission
        current_user_role = get_user_current_role(request.user)
        if not current_user_role:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa người dùng'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Bo can edit all users
        if is_bo_user(request.user):
            pass
        # Admin can only edit users in their organization
        elif is_co_quan_user(request.user):
            user_role = get_user_current_role(user)
            if not user_role or user_role.organization != current_user_role.organization:
                return Response(
                    {'error': 'Bạn không có quyền chỉnh sửa người dùng này'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Bạn không có quyền chỉnh sửa người dùng'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update user basic fields
        data = request.data
        
        if 'full_name' in data:
            names = data['full_name'].strip().split(maxsplit=1)
            user.first_name = names[0] if len(names) > 0 else ''
            user.last_name = names[1] if len(names) > 1 else ''
        
        if 'email' in data and data['email'] != user.email:
            # Validate email
            try:
                validate_email(data['email'])
                # Check if email already exists
                if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                    return Response(
                        {'error': 'Email đã được sử dụng'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.email = data['email']
            except ValidationError:
                return Response(
                    {'error': 'Email không hợp lệ'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user.save()
        
        # Update user profile (including name and meta)
        from common.djangoapps.student.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Update profile name
            if 'full_name' in data:
                profile.name = data['full_name'].strip()
            
            # Handle meta field - it might be a string (JSON) or dict
            if hasattr(profile, 'meta') and profile.meta:
                if isinstance(profile.meta, str):
                    try:
                        meta = json.loads(profile.meta)
                    except (json.JSONDecodeError, ValueError):
                        meta = {}
                elif isinstance(profile.meta, dict):
                    meta = profile.meta
                else:
                    meta = {}
            else:
                meta = {}
            
            # Update meta fields
            meta_fields = [
                'phone', 'gender', 'ngay_sinh', 'cccd', 'ngay_cap_cccd',
                'don_vi_cong_tac', 'que_quan', 'dan_toc', 'ghi_chu',
                'avatar_url', 'vi_tri_viec_lam', 'chuc_vu', 'nguoi_nhan_bang',
                'so_chung_chi', 'ten_khoa_hoc', 'thoi_gian_hoc', 'nam_tot_nghiep',
                'so_tiet_quy_doi', 'loai_hinh_dao_tao', 'noi_sinh', 'dia_chi',
                'so_nam_cong_tac'
            ]
            
            for field in meta_fields:
                if field in data:
                    meta[field] = data[field]
            
            # Convert meta back to JSON string if needed
            profile.meta = json.dumps(meta) if meta else '{}'
            profile.save()
            
        except UserProfile.DoesNotExist:
            pass
        
        # Update role and organization if provided (only Bo can do this)
        if is_bo_user(request.user):
            # Accept both 'role' and 'user_role' field names
            new_role = data.get('role') or data.get('user_role')
            # Accept both 'organization' and 'organization_id' field names
            new_org_id = data.get('organization') or data.get('organization_id')
            
            if new_role or new_org_id is not None:
                user_role = get_user_current_role(user)
                
                # Create new role object if it doesn't exist
                if not user_role:
                    user_role = ChalixUserRole(user=user)
                
                # Update role if provided
                if new_role:
                    user_role.role = new_role
                
                # Update organization if provided
                if new_org_id is not None:
                    if new_org_id:
                        try:
                            org = ChalixOrganization.objects.get(id=new_org_id)
                            user_role.organization = org
                        except ChalixOrganization.DoesNotExist:
                            return Response(
                                {'error': 'Không tìm thấy cơ quan'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        user_role.organization = None
                
                # Save the role
                user_role.save()
        
        return Response({
            'success': True,
            'message': 'Cập nhật người dùng thành công'
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Không tìm thấy người dùng'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        log.error(f'Error updating user: {str(e)}')
        return Response(
            {'error': f'Lỗi khi cập nhật người dùng: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )