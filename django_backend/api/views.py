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
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import inch
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

# Create uploads directory
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Public health check endpoint for deployment platforms"""
    return Response({'status': 'healthy', 'service': 'chemical-backend'}, status=status.HTTP_200_OK)

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
def get_dataset_detail(request, dataset_id):
    """Get specific dataset with raw data"""
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        
        # Read the CSV file to get raw data
        df = pd.read_csv(dataset.file_path)
        
        serializer = DatasetSummarySerializer(dataset)
        return Response({
            'summary': serializer.data,
            'raw_data': df.to_dict('records')
        }, status=status.HTTP_200_OK)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

def create_chart(chart_type, data, title, xlabel, ylabel):
    """Helper function to create chart images for PDF"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    if chart_type == 'bar':
        labels = list(data.keys())
        values = list(data.values())
        ax.bar(labels, values, color='#3b82f6')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=45, ha='right')
    elif chart_type == 'pie':
        labels = list(data.keys())
        values = list(data.values())
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
    
    ax.set_title(title, fontweight='bold', fontsize=12)
    plt.tight_layout()
    
    # Save to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    return Image(img_buffer, width=5*inch, height=3.5*inch)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_pdf_report(request, dataset_id=None):
    """Generate comprehensive PDF report with units, charts, and tables"""
    try:
        if dataset_id:
            dataset = Dataset.objects.get(id=dataset_id)
        else:
            dataset = Dataset.objects.first()
        
        if not dataset:
            return Response({'error': 'No dataset found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Read the CSV file to get raw data
        df = pd.read_csv(dataset.file_path)
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>Chemical Equipment Analysis Report</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Dataset info
        info = Paragraph(f"<b>Dataset:</b> {dataset.name}<br/>"
                        f"<b>Upload Date:</b> {dataset.upload_timestamp.strftime('%Y-%m-%d %H:%M')}<br/>"
                        f"<b>Total Equipment Count:</b> {dataset.total_equipment_count}",
                        styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary statistics with UNITS
        summary_title = Paragraph("<b>Summary Statistics</b>", styles['Heading2'])
        elements.append(summary_title)
        elements.append(Spacer(1, 0.15*inch))
        
        summary_data = [
            ['Metric', 'Value', 'Unit'],
            ['Average Flowrate', f"{dataset.avg_flowrate:.2f}", 'L/min'],
            ['Average Pressure', f"{dataset.avg_pressure:.2f}", 'psi'],
            ['Average Temperature', f"{dataset.avg_temperature:.2f}", '°C']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white])
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Equipment type distribution
        dist_title = Paragraph("<b>Equipment Type Distribution</b>", styles['Heading2'])
        elements.append(dist_title)
        elements.append(Spacer(1, 0.15*inch))
        
        dist_data = [['Equipment Type', 'Count', 'Percentage']]
        total_count = sum(dataset.equipment_type_distribution.values())
        for equip_type, count in dataset.equipment_type_distribution.items():
            percentage = (count / total_count) * 100
            dist_data.append([equip_type, str(count), f"{percentage:.1f}%"])
        
        dist_table = Table(dist_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white])
        ]))
        elements.append(dist_table)
        elements.append(PageBreak())
        
        # CHARTS SECTION
        charts_title = Paragraph("<b>Visual Analysis</b>", styles['Heading1'])
        elements.append(charts_title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Chart 1: Equipment Type Distribution (Pie Chart)
        chart1_title = Paragraph("<b>Equipment Type Distribution</b>", styles['Heading3'])
        elements.append(chart1_title)
        elements.append(Spacer(1, 0.1*inch))
        chart1 = create_chart('pie', dataset.equipment_type_distribution, 
                             'Equipment Type Distribution', '', '')
        elements.append(chart1)
        elements.append(Spacer(1, 0.3*inch))
        
        # Chart 2: Equipment Type Count (Bar Chart)
        chart2_title = Paragraph("<b>Equipment Count by Type</b>", styles['Heading3'])
        elements.append(chart2_title)
        elements.append(Spacer(1, 0.1*inch))
        chart2 = create_chart('bar', dataset.equipment_type_distribution,
                             'Equipment Count by Type', 'Equipment Type', 'Count')
        elements.append(chart2)
        elements.append(PageBreak())
        
        # Chart 3: Average Parameters by Equipment Type (Bar Chart)
        chart3_title = Paragraph("<b>Average Flowrate by Equipment Type</b>", styles['Heading3'])
        elements.append(chart3_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Calculate average flowrate per equipment type
        avg_flowrate_by_type = df.groupby('Equipment Type')['Flowrate'].mean().to_dict()
        chart3 = create_chart('bar', avg_flowrate_by_type,
                             'Average Flowrate by Equipment Type', 'Equipment Type', 'Flowrate (L/min)')
        elements.append(chart3)
        elements.append(Spacer(1, 0.3*inch))
        
        # Chart 4: Average Pressure by Equipment Type
        chart4_title = Paragraph("<b>Average Pressure by Equipment Type</b>", styles['Heading3'])
        elements.append(chart4_title)
        elements.append(Spacer(1, 0.1*inch))
        
        avg_pressure_by_type = df.groupby('Equipment Type')['Pressure'].mean().to_dict()
        chart4 = create_chart('bar', avg_pressure_by_type,
                             'Average Pressure by Equipment Type', 'Equipment Type', 'Pressure (psi)')
        elements.append(chart4)
        elements.append(PageBreak())
        
        # Chart 5: Average Temperature by Equipment Type
        chart5_title = Paragraph("<b>Average Temperature by Equipment Type</b>", styles['Heading3'])
        elements.append(chart5_title)
        elements.append(Spacer(1, 0.1*inch))
        
        avg_temp_by_type = df.groupby('Equipment Type')['Temperature'].mean().to_dict()
        chart5 = create_chart('bar', avg_temp_by_type,
                             'Average Temperature by Equipment Type', 'Equipment Type', 'Temperature (°C)')
        elements.append(chart5)
        elements.append(Spacer(1, 0.3*inch))
        
        # Chart 6: Flowrate Performance Trend (All Data)
        chart6_title = Paragraph("<b>Flowrate Performance Trend (All Equipment)</b>", styles['Heading3'])
        elements.append(chart6_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Create line chart with all flowrate data
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(range(len(df)), df['Flowrate'], color='#4FC3F7', linewidth=1.5, alpha=0.8)
        ax.fill_between(range(len(df)), df['Flowrate'], alpha=0.3, color='#4FC3F7')
        ax.set_xlabel('Equipment Index', fontsize=10)
        ax.set_ylabel('Flowrate (L/min)', fontsize=10)
        ax.set_title('Flowrate Performance Trend', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        elements.append(Image(img_buffer, width=5*inch, height=3.5*inch))
        elements.append(PageBreak())
        
        # Chart 7: Temperature vs Pressure Analysis (All Data)
        chart7_title = Paragraph("<b>Temperature vs Pressure Analysis (All Equipment)</b>", styles['Heading3'])
        elements.append(chart7_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # Create scatter plot with all data
        fig, ax = plt.subplots(figsize=(6, 4))
        scatter = ax.scatter(df['Temperature'], df['Pressure'], 
                           c=df['Flowrate'], cmap='coolwarm', 
                           alpha=0.6, s=50, edgecolors='white', linewidth=0.5)
        ax.set_xlabel('Temperature (°C)', fontsize=10)
        ax.set_ylabel('Pressure (psi)', fontsize=10)
        ax.set_title('Temperature vs Pressure Analysis', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Flowrate (L/min)', fontsize=9)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        elements.append(Image(img_buffer, width=5*inch, height=3.5*inch))
        elements.append(Spacer(1, 0.4*inch))
        
        # RAW DATA TABLE with UNITS
        table_title = Paragraph("<b>Detailed Equipment Data</b>", styles['Heading1'])
        elements.append(table_title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Prepare table data with units in headers
        table_data = [['Equipment Name', 'Equipment Type', 'Flowrate\n(L/min)', 'Pressure\n(psi)', 'Temperature\n(°C)']]
        
        # Add all rows of data
        for idx, row in df.iterrows():
            table_data.append([
                str(row['Equipment Name'])[:30],  # Truncate long names
                str(row['Equipment Type']),
                f"{row['Flowrate']:.2f}",
                f"{row['Pressure']:.2f}",
                f"{row['Temperature']:.2f}"
            ])
        
        # Create table with appropriate column widths
        col_widths = [1.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch]
        data_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.append(data_table)
        
        # Footer note showing total rows
        elements.append(Spacer(1, 0.2*inch))
        footer_note = Paragraph(f"<i>Total rows displayed: {len(df)}</i>", 
                               styles['Normal'])
        elements.append(footer_note)
        
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
