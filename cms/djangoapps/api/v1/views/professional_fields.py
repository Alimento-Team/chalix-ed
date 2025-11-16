from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import IntegrityError
from cms.djangoapps.contentstore.models import ProfessionalField
from ..serializers.professional_fields import ProfessionalFieldSerializer


class ProfessionalFieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Professional Fields (Lĩnh vực chuyên môn).
    Only Bộ role can create, update, and delete.
    All authenticated users can list active fields.
    Professional fields are global, not organization-specific.
    """
    queryset = ProfessionalField.objects.all()
    serializer_class = ProfessionalFieldSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return all active professional fields.
        Professional fields are now global, not organization-specific.
        """
        # All authenticated users can see active fields
        return ProfessionalField.objects.filter(is_active=True).order_by('sort_order', 'name')

    def create(self, request, *args, **kwargs):
        """Only Bộ (superusers/staff) can create professional fields"""
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {"error": "Only Bộ role can create professional fields"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set created_by from request user
        data = request.data.copy()
        data['created_by'] = request.user.username
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            # Catch any database-level unique constraint violations
            return Response(
                {"name": ["A professional field with this name already exists"]},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Only Bộ (superusers/staff) can update professional fields"""
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {"error": "Only Bộ role can update professional fields"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"name": ["A professional field with this name already exists"]},
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """Only Bộ (superusers/staff) can update professional fields"""
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {"error": "Only Bộ role can update professional fields"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            return super().partial_update(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"name": ["A professional field with this name already exists"]},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """Only Bộ (superusers/staff) can delete professional fields"""
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {"error": "Only Bộ role can delete professional fields"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete by setting is_active to False
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """List professional fields with permission info"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        data = {
            'professional_fields': serializer.data,
            'can_manage': request.user.is_superuser or request.user.is_staff,
            'is_bo': request.user.is_superuser or request.user.is_staff
        }
        
        return Response(data)
