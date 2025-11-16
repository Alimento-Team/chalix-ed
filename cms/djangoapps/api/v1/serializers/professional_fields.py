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
        """Ensure name is not empty and unique"""
        if not value or not value.strip():
            raise serializers.ValidationError("Professional field name cannot be empty")
        
        # Check for uniqueness
        name = value.strip()
        queryset = ProfessionalField.objects.filter(name=name)
        
        # If updating, exclude the current instance
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A professional field with this name already exists")
        
        return name
