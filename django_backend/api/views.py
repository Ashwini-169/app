from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.http import HttpResponse, FileResponse
from .models import Dataset
from .serializers import DatasetSerializer, DatasetSummarySerializer
import pandas as pd
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import io

# Create uploads directory
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    """Upload and process CSV file"""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    dataset_name = request.data.get('name', csv_file.name)
    
    # Validate file extension
    if not csv_file.name.endswith('.csv'):
        return Response({'error': 'Only CSV files are allowed'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Read CSV using pandas
        df = pd.read_csv(csv_file)
        
        # Validate required columns
        required_columns = ['Equipment Name', 'Equipment Type', 'Flowrate', 'Pressure', 'Temperature']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Clean data - remove any rows with missing critical values
        df_clean = df.dropna(subset=['Flowrate', 'Pressure', 'Temperature'])
        
        if len(df_clean) == 0:
            return Response({'error': 'No valid data rows found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate statistics
        total_count = len(df_clean)
        avg_flowrate = float(df_clean['Flowrate'].mean())
        avg_pressure = float(df_clean['Pressure'].mean())
        avg_temperature = float(df_clean['Temperature'].mean())
        
        # Equipment type distribution
        type_distribution = df_clean['Equipment Type'].value_counts().to_dict()
        
        # Save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{csv_file.name}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        with open(file_path, 'wb+') as destination:
            for chunk in csv_file.chunks():
                destination.write(chunk)
        
        # Create dataset record
        dataset = Dataset.objects.create(
            name=dataset_name,
            total_equipment_count=total_count,
            avg_flowrate=avg_flowrate,
            avg_pressure=avg_pressure,
            avg_temperature=avg_temperature,
            equipment_type_distribution=type_distribution,
            file_path=file_path,
            uploaded_by=request.user
        )
        
        # Maintain only last 5 datasets
        Dataset.maintain_dataset_limit(5)
        
        serializer = DatasetSerializer(dataset)
        return Response({
            'message': 'File uploaded successfully',
            'dataset': serializer.data,
            'raw_data': df_clean.to_dict('records')[:100]  # Return first 100 rows
        }, status=status.HTTP_201_CREATED)
        
    except pd.errors.EmptyDataError:
        return Response({'error': 'CSV file is empty'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_summary(request):
    """Get summary of the latest dataset"""
    try:
        latest_dataset = Dataset.objects.first()
        if not latest_dataset:
            return Response({'error': 'No datasets found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Read the CSV file to get raw data
        df = pd.read_csv(latest_dataset.file_path)
        
        serializer = DatasetSummarySerializer(latest_dataset)
        return Response({
            'summary': serializer.data,
            'raw_data': df.to_dict('records')
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_history(request):
    """Get history of all datasets (last 5)"""
    datasets = Dataset.objects.all()[:5]
    serializer = DatasetSerializer(datasets, many=True)
    return Response({'history': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request, dataset_id=None):
    """Export dataset as CSV"""
    try:
        if dataset_id:
            dataset = Dataset.objects.get(id=dataset_id)
        else:
            dataset = Dataset.objects.first()
        
        if not dataset:
            return Response({'error': 'No dataset found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Read the original CSV
        df = pd.read_csv(dataset.file_path)
        
        # Create response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{dataset.name}.csv"'
        df.to_csv(response, index=False)
        
        return response
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_pdf_report(request, dataset_id=None):
    """Generate PDF report for a dataset"""
    try:
        if dataset_id:
            dataset = Dataset.objects.get(id=dataset_id)
        else:
            dataset = Dataset.objects.first()
        
        if not dataset:
            return Response({'error': 'No dataset found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Chemical Equipment Analysis Report</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Dataset info
        info = Paragraph(f"<b>Dataset:</b> {dataset.name}<br/>"
                        f"<b>Upload Date:</b> {dataset.upload_timestamp.strftime('%Y-%m-%d %H:%M')}<br/>"
                        f"<b>Total Equipment Count:</b> {dataset.total_equipment_count}",
                        styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary statistics
        summary_title = Paragraph("<b>Summary Statistics</b>", styles['Heading2'])
        elements.append(summary_title)
        elements.append(Spacer(1, 0.2*inch))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Average Flowrate', f"{dataset.avg_flowrate:.2f}"],
            ['Average Pressure', f"{dataset.avg_pressure:.2f}"],
            ['Average Temperature', f"{dataset.avg_temperature:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Equipment type distribution
        dist_title = Paragraph("<b>Equipment Type Distribution</b>", styles['Heading2'])
        elements.append(dist_title)
        elements.append(Spacer(1, 0.2*inch))
        
        dist_data = [['Equipment Type', 'Count']]
        for equip_type, count in dataset.equipment_type_distribution.items():
            dist_data.append([equip_type, str(count)])
        
        dist_table = Table(dist_data, colWidths=[3*inch, 2*inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(dist_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{dataset.name}_report.pdf"'
        
        return response
        
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email)
    return Response({
        'message': 'User registered successfully',
        'user': {'id': user.id, 'username': user.username, 'email': user.email}
    }, status=status.HTTP_201_CREATED)
