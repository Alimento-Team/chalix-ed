from rest_framework import serializers
from cms.djangoapps.contentstore.models import ChalixOrganization
from django.contrib.auth.models import User


class OrganizationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True, allow_null=True)
    admin_email = serializers.CharField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = ChalixOrganization
        fields = [
            'id', 'name', 'display_name', 'code', 'description', 
            'is_active', 'admin', 'admin_username', 'admin_email',
            'parent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
