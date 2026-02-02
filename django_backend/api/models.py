from django.db import models
from django.contrib.auth.models import User
import json

class Dataset(models.Model):
    name = models.CharField(max_length=255)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    total_equipment_count = models.IntegerField()
    avg_flowrate = models.FloatField()
    avg_pressure = models.FloatField()
    avg_temperature = models.FloatField()
    equipment_type_distribution = models.JSONField()
    file_path = models.CharField(max_length=500)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-upload_timestamp']
    
    def __str__(self):
        return f"{self.name} - {self.upload_timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def maintain_dataset_limit(cls, limit=5):
        """Keep only the last N datasets"""
        datasets = cls.objects.all().order_by('-upload_timestamp')
        if datasets.count() > limit:
            datasets_to_delete = datasets[limit:]
            for dataset in datasets_to_delete:
                dataset.delete()
