from rest_framework import serializers
from cms.djangoapps.contentstore.models import Organization
from django.contrib.auth.models import User


class OrganizationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True, allow_null=True)
    admin_email = serializers.CharField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'admin', 'admin_username', 'admin_email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
