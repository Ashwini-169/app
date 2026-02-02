from rest_framework import serializers
from .models import Dataset
from django.contrib.auth.models import User

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'upload_timestamp', 'total_equipment_count', 
                  'avg_flowrate', 'avg_pressure', 'avg_temperature', 
                  'equipment_type_distribution', 'file_path']
        read_only_fields = ['id', 'upload_timestamp']

class DatasetSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'upload_timestamp', 'total_equipment_count', 
                  'avg_flowrate', 'avg_pressure', 'avg_temperature', 
                  'equipment_type_distribution']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
