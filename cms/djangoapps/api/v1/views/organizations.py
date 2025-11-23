from rest_framework import viewsets, permissions
from cms.djangoapps.contentstore.models import ChalixOrganization
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from ..serializers.organizations import OrganizationSerializer
from cms.djangoapps.contentstore.chalix_roles import is_bo_user
from common.djangoapps.student.roles import GlobalStaff


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = ChalixOrganization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return all organizations for superusers (Bộ),
        or only the organization they admin for regular users.
        """
        user = self.request.user
        # Check if user is GlobalStaff or has 'bo' role
        if is_bo_user(user):
            # Bộ can see all active organizations
            return ChalixOrganization.objects.filter(is_active=True)
        else:
            # Regular users can only see their own organization
            return ChalixOrganization.objects.filter(admin=user, is_active=True)

    def create(self, request, *args, **kwargs):
        # Only superusers or 'bo' role can create organizations
        if not is_bo_user(request.user):
            return Response(
                {"error": "Only Bộ (superusers) can create organizations"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Bộ can update any organization.
        Admin can only update their own organization.
        """
        instance = self.get_object()
        user = request.user
        
        # Check if user is Bộ (can edit all)
        if is_bo_user(user):
            pass  # Allow
        # Admin can only edit their own organization
        elif instance.admin == user:
            pass  # Allow
        else:
            return Response(
                {"error": "You don't have permission to edit this organization"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Only Bộ (superusers) can delete organizations"""
        if not is_bo_user(request.user):
            return Response(
                {"error": "Only Bộ (superusers) can delete organizations"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        # Check if user is Bộ
        user_is_bo = is_bo_user(request.user)
        
        # Add user permission info to response
        data = {
            'organizations': serializer.data,
            'can_create': user_is_bo,
            'is_bo': user_is_bo
        }
        return Response(data)

    @action(detail=False, methods=['get'], url_path='staff-users')
    def staff_users(self, request):
        """
        Return list of all active users that can be assigned as organization admins.
        Only accessible by Bộ (superusers/staff).
        """
        # Check if user is Bộ role
        if not is_bo_user(request.user):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.contrib.auth.models import User
        
        # Get all active users (Bộ can assign anyone as organization admin)
        # Exclude superusers to prevent accidental assignment
        users = User.objects.filter(
            is_active=True,
            is_superuser=False
        ).order_by('username')[:200]  # Limit to 200 users for performance
        
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name() or user.username
        } for user in users]
        
        return Response({'users': users_data})
