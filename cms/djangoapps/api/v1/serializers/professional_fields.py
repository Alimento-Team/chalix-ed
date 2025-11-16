from rest_framework import serializers
from cms.djangoapps.contentstore.models import ProfessionalField


class ProfessionalFieldSerializer(serializers.ModelSerializer):
    """Serializer for ProfessionalField model"""
    
    class Meta:
        model = ProfessionalField
        fields = [
            'id',
            'name',
            'description',
            'is_active',
            'sort_order',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Ensure name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Professional field name cannot be empty")
        return value.strip()
