from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('summary/latest/', views.get_latest_summary, name='latest_summary'),
    path('history/', views.get_history, name='history'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/csv/<int:dataset_id>/', views.export_csv, name='export_csv_by_id'),
    path('report/pdf/', views.generate_pdf_report, name='pdf_report'),
    path('report/pdf/<int:dataset_id>/', views.generate_pdf_report, name='pdf_report_by_id'),
    path('register/', views.register_user, name='register'),
]
