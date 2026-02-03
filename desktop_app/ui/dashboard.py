"""
Dashboard - Main application window with MVC pattern
Matches React web app styling from App.css
"""

import sys
import csv
import io
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QListWidgetItem, QProgressBar, QSplitter,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QColor
import traceback

# Import existing chart module (avoid duplication)
from charts.plots import create_pie_chart, create_bar_chart, create_scatter_plot, create_flowrate_trend
from ui.data_table import DataTableDialog


# Worker threads for async operations
class HistoryLoaderThread(QThread):
    """Background thread to load history data"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
    
    def run(self):
        try:
            result = self.api_client.get_history()
            if result.get("success"):
                self.finished.emit(result.get("data", []))
            else:
                self.error.emit(result.get("message", "Failed to load history"))
        except Exception as e:
            self.error.emit(f"Error loading history: {str(e)}")

class UploadThread(QThread):
    """Background thread for CSV upload"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, api_client, file_path, dataset_name):
        super().__init__()
        self.api_client = api_client
        self.file_path = file_path
        self.dataset_name = dataset_name
    
    def run(self):
        try:
            self.progress.emit(50)
            result = self.api_client.upload_csv(self.file_path, self.dataset_name)
            self.progress.emit(100)
            
            if result.get("success"):
                self.finished.emit(result.get("data", {}))
            else:
                self.error.emit(result.get("message", "Upload failed"))
        except Exception as e:
            self.error.emit(f"Error uploading file: {str(e)}")


class ExportThread(QThread):
    """Background thread for CSV/PDF export"""
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)
    
    def __init__(self, api_client, dataset_id, export_type):
        super().__init__()
        self.api_client = api_client
        self.dataset_id = dataset_id
        self.export_type = export_type  # "csv" or "pdf"
    
    def run(self):
        try:
            if self.export_type == "csv":
                result = self.api_client.export_csv(self.dataset_id)
            else:
                result = self.api_client.export_pdf(self.dataset_id)
            
            if result.get("success"):
                self.finished.emit(result.get("data"))
            else:
                self.error.emit(result.get("message", "Export failed"))
        except Exception as e:
            self.error.emit(f"Error exporting: {str(e)}")


class Dashboard(QMainWindow):
    """
    Main dashboard window matching React app design
    Features: History list, Summary cards, Charts, Export functionality
    """
    
    def __init__(self, api_client, auth_manager, username):
        super().__init__()
        self.api_client = api_client
        self.auth_manager = auth_manager
        self.username = username
        
        # Current state
        self.current_dataset_id = None
        self.current_summary = None
        self.history_data = []
        
        # Worker threads
        self.active_threads = []
        
        self.init_ui()
        self.apply_styling()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialize UI components with sidebar layout"""
        self.setWindowTitle("Chemical Equipment Parameter Visualizer - Dashboard")
        self.setGeometry(100, 100, 1600, 900)

        # Central widget with objectName and styled background
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Horizontal splitter: Left sidebar + Right main area
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        
        # Left Panel: History and Filters
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right Panel: Main content area (upload, summary, charts)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (left: 400px, right: rest)
        splitter.setSizes([300, 1300])
        splitter.setStretchFactor(0, 0)  # Left panel fixed
        splitter.setStretchFactor(1, 1)  # Right panel stretches
        
        main_layout.addWidget(splitter)
    
    def create_header(self):
        """Create dashboard header matching React design"""
        header = QFrame()
        header.setObjectName("dashboardHeader")
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(72)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setAlignment(Qt.AlignVCenter)
        
        # Left side - Title
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        
        title = QLabel("Chemical Equipment Dashboard")
        title.setObjectName("headerTitle")
        subtitle = QLabel(f"Welcome, {self.username}")
        subtitle.setObjectName("headerSubtitle")
        
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        
        # Right side - Action buttons
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        self.btn_view_data = QPushButton("📋 View Raw Data")
        self.btn_view_data.setObjectName("btnSecondary")
        self.btn_view_data.setEnabled(False)
        self.btn_view_data.clicked.connect(self.handle_view_raw_data)
        
        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.setObjectName("btnSecondary")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(self.handle_export_csv)
        
        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.setObjectName("btnSecondary")
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.clicked.connect(self.handle_export_pdf)
        
        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("btnLogout")
        btn_logout.clicked.connect(self.handle_logout)
        
        right_layout.addWidget(self.btn_view_data)
        right_layout.addWidget(self.btn_export_csv)
        right_layout.addWidget(self.btn_export_pdf)
        right_layout.addWidget(btn_logout)
        
        layout.addWidget(left_widget)
        layout.addStretch()
        layout.addWidget(right_widget)
        
        return header
    
    def create_left_panel(self):
        """Create left sidebar with history and filters"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(380)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # History section
        self.history_widget = self.create_history_section()
        layout.addWidget(self.history_widget)
        
        return panel
    
    def create_right_panel(self):
        """Create right main content area"""
        panel = QWidget()
        panel.setObjectName("rightPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("scrollArea")
        
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Upload section
        upload_section = self.create_upload_section()
        content_layout.addWidget(upload_section)
        
        # Summary cards
        self.summary_cards_widget = self.create_summary_cards()
        content_layout.addWidget(self.summary_cards_widget)
        
        # Charts section with real matplotlib charts
        self.charts_widget = self.create_charts_section()
        content_layout.addWidget(self.charts_widget)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        return panel
    
    def create_upload_section(self):
        """Create CSV upload section"""
        section = QFrame()
        section.setObjectName("uploadSection")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("Upload New Dataset")
        title.setObjectName("sectionTitle")

        # Header row: title left, dataset context right
        header_row = QHBoxLayout()
        header_row.addWidget(title)
        header_row.addStretch()

        self.dataset_context_widget = self.create_dataset_context()
        self.dataset_context_widget.setVisible(False)
        header_row.addWidget(self.dataset_context_widget)

        layout.addLayout(header_row)
        
        # Upload form
        form_layout = QHBoxLayout()
        form_layout.setSpacing(16)
        
        self.btn_select_file = QPushButton("Select CSV File")
        self.btn_select_file.setObjectName("btnSecondary")
        self.btn_select_file.setMinimumWidth(200)
        self.btn_select_file.clicked.connect(self.select_file)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("fileLabel")
        
        self.btn_upload = QPushButton("Upload & Analyze")
        self.btn_upload.setObjectName("btnUpload")
        self.btn_upload.setEnabled(False)
        self.btn_upload.clicked.connect(self.handle_upload)
        
        self.upload_progress = QProgressBar()
        self.upload_progress.setObjectName("uploadProgress")
        self.upload_progress.setVisible(False)
        self.upload_progress.setMaximumHeight(8)
        
        form_layout.addWidget(self.btn_select_file)
        form_layout.addWidget(self.file_label, 1)
        form_layout.addWidget(self.btn_upload)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.upload_progress)
        
        self.selected_file_path = None
        
        return section
    
    def create_dataset_context(self):
        """Create dataset context banner showing current dataset info"""
        container = QFrame()
        container.setObjectName("datasetContext")
        container.setVisible(False)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel("📊")
        icon_label.setObjectName("datasetIcon")
        icon_label.setStyleSheet("font-size: 20px;")
        
        # Dataset info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        self.dataset_name_label = QLabel("No dataset selected")
        self.dataset_name_label.setObjectName("datasetContextName")
        
        self.dataset_timestamp_label = QLabel("")
        self.dataset_timestamp_label.setObjectName("datasetContextTimestamp")
        
        info_layout.addWidget(self.dataset_name_label)
        info_layout.addWidget(self.dataset_timestamp_label)
        
        # Active badge
        self.active_badge = QLabel("● ACTIVE")
        self.active_badge.setObjectName("activeBadge")
        
        layout.addWidget(icon_label)
        layout.addWidget(info_widget, 1)
        layout.addWidget(self.active_badge)
        
        return container
    
    def create_summary_cards(self):
        """Create summary statistics cards"""
        container = QFrame()
        container.setObjectName("summaryContainer")
        
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Create 4 stat cards with units
        self.card_total = self.create_stat_card("Total Equipment", "0")
        self.card_flowrate = self.create_stat_card("Avg Flowrate (L/min)", "0.00")
        self.card_pressure = self.create_stat_card("Avg Pressure (psi)", "0.00")
        self.card_temperature = self.create_stat_card("Avg Temperature (°F)", "0.00")
        
        layout.addWidget(self.card_total, 0, 0)
        layout.addWidget(self.card_flowrate, 0, 1)
        layout.addWidget(self.card_pressure, 0, 2)
        layout.addWidget(self.card_temperature, 0, 3)
        
        # Initially hidden
        container.setVisible(False)
        
        return container
    
    def create_stat_card(self, label_text, value_text):
        """Create individual stat card"""
        card = QFrame()
        card.setObjectName("statCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("statLabel")
        
        value = QLabel(value_text)
        value.setObjectName("statValue")
        
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addStretch()
        
        return card
    
    def create_charts_section(self):
        """Create charts display section with scroll support"""
        section = QFrame()
        section.setObjectName("chartsSection")
        section.setVisible(False)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("Data Visualization")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Scroll area for charts (handles overflow)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # FIX 3
        
        # Container widget for vertical chart stack
        charts_widget = QWidget()
        charts_widget.setMinimumWidth(1200)
        charts_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # POLISH A
        self.charts_container = QVBoxLayout(charts_widget)
        self.charts_container.setSpacing(16)
        self.charts_container.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(charts_widget)
        layout.addWidget(scroll_area, 1) # FIX 2
        
        return section
    
    def create_history_section(self):
        """Create upload history section for sidebar"""
        section = QFrame()
        section.setObjectName("historySection")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        title = QLabel("Upload History")
        title.setObjectName("historySectionTitle")
        layout.addWidget(title)
        
        subtitle = QLabel("Last 5 Datasets")
        subtitle.setObjectName("historySubtitle")
        layout.addWidget(subtitle)
        
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setSpacing(8)
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        
        layout.addWidget(self.history_list)
        
        # Initially show empty state
        section.setVisible(False)
        
        return section
    
    def _create_stat_widget(self, label_text, value_text):
        """Helper: Create a small stat widget (reduces duplication)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        label = QLabel(label_text)
        label.setObjectName("historyStatLabel")
        value = QLabel(value_text)
        value.setObjectName("historyStatValue")
        
        layout.addWidget(label)
        layout.addWidget(value)
        
        return widget
    
    def create_history_item_widget(self, dataset):
        """Create custom widget for history list item matching React cards"""
        widget = QFrame()
        widget.setObjectName("historyCard")
        # Store dataset ID for active state tracking
        widget.setProperty("datasetId", dataset.get("id"))
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)
        
        name_label = QLabel(dataset.get("name", "Unknown"))
        name_label.setObjectName("historyCardTitle")
        
        date_label = QLabel(dataset.get("upload_timestamp", ""))
        date_label.setObjectName("historyCardDate")
        
        header_layout.addWidget(name_label)
        header_layout.addWidget(date_label)
        
        # Stats grid - using helper method to reduce duplication
        stats_layout = QGridLayout()
        stats_layout.setSpacing(12)
        
        stats_data = [
            ("Equipment Count", str(dataset.get("total_equipment_count", 0))),
            ("Avg Flowrate", f"{dataset.get('avg_flowrate', 0):.2f}"),
            ("Avg Pressure", f"{dataset.get('avg_pressure', 0):.2f}"),
            ("Avg Temperature", f"{dataset.get('avg_temperature', 0):.2f}")
        ]
        
        for i, (label, value) in enumerate(stats_data):
            stat_widget = self._create_stat_widget(label, value)
            row, col = divmod(i, 2)
            stats_layout.addWidget(stat_widget, row, col)
        
        # Action buttons - using list comprehension for cleaner code
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        buttons = [
            ("View Analysis", "btnSmallPrimary", lambda: self.load_dataset_by_id(dataset.get("id"))),
            ("CSV", "btnSmallSecondary", lambda: self.export_dataset(dataset.get("id"), "csv")),
            ("PDF", "btnSmallSecondary", lambda: self.export_dataset(dataset.get("id"), "pdf"))
        ]
        
        for text, style, handler in buttons:
            btn = QPushButton(text)
            btn.setObjectName(style)
            btn.clicked.connect(handler)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        
        # Assemble
        layout.addLayout(header_layout)
        layout.addLayout(stats_layout)
        layout.addLayout(actions_layout)
        
        return widget
    
    # ===== Data Loading Methods =====
    
    def load_initial_data(self):
        """Load history and latest summary on startup"""
        self.load_history()
    
    def load_history(self):
        """Load upload history in background thread"""
        thread = HistoryLoaderThread(self.api_client)
        thread.finished.connect(self.on_history_loaded)
        thread.error.connect(self.on_error)
        thread.start()
        
        self.active_threads.append(thread)
    
    def on_history_loaded(self, history_data):
        """Handle history data loaded"""
        self.history_data = history_data
        self.history_list.clear()
        
        if history_data:
            self.history_widget.setVisible(True)
            
            for dataset in history_data:
                item = QListWidgetItem(self.history_list)
                item_widget = self.create_history_item_widget(dataset)
                
                item.setSizeHint(item_widget.sizeHint())
                self.history_list.addItem(item)
                self.history_list.setItemWidget(item, item_widget)
            
            # Load latest dataset automatically (like React does)
            if history_data:
                self.load_dataset_by_id(history_data[0].get("id"))
                # Also set current dataset ID for exports
                self.current_dataset_id = history_data[0].get("id")
                # Highlight active card
                self.update_active_history_card()
    
    def load_dataset_by_id(self, dataset_id):
        """Load specific dataset summary using history data (like React app)"""
        self.current_dataset_id = dataset_id
        
        # Find dataset in history
        dataset = None
        for item in self.history_data:
            if item.get('id') == dataset_id:
                dataset = item
                break
        
        if not dataset:
            self.on_error("Dataset not found in history")
            return
        
        # Update summary display with dataset info (like React does)
        summary_data = {
            'total_equipment_count': dataset.get('total_equipment_count', 0),
            'avg_flowrate': dataset.get('avg_flowrate', 0),
            'avg_pressure': dataset.get('avg_pressure', 0),
            'avg_temperature': dataset.get('avg_temperature', 0),
            'equipment_type_distribution': dataset.get('equipment_type_distribution', {}),
            'name': dataset.get('name', 'Unknown'),
            'id': dataset.get('id')
        }
        
        # Try to fetch CSV for raw data (for charts)
        # This matches React's handleHistoryClick behavior
        try:
            result = self.api_client.export_csv(dataset_id)
            if result.get('success') and result.get('data'):
                raw_data = self._parse_csv_bytes(result.get('data'))
                self.update_summary_display({'summary': summary_data, 'raw_data': raw_data})
            else:
                # If CSV fetch fails, just update summary without raw data (like React fallback)
                self.update_summary_display({'summary': summary_data, 'raw_data': []})
        except Exception:
            # Fallback: update with summary only (like React error handler)
            self.update_summary_display({'summary': summary_data, 'raw_data': []})
        
        # Enable export and view data buttons
        self.btn_export_csv.setEnabled(True)
        self.btn_export_pdf.setEnabled(True)
        self.btn_view_data.setEnabled(True)
        
        # Update dataset context banner
        self.update_dataset_context(dataset)
        
        # Highlight active history card
        self.update_active_history_card()
    
    def update_dataset_context(self, dataset):
        """Update dataset context banner with current dataset info"""
        if dataset:
            self.dataset_name_label.setText(f"Dataset: {dataset.get('name', 'Unknown')}")
            timestamp = dataset.get('upload_timestamp', '')
            self.dataset_timestamp_label.setText(f"Uploaded: {timestamp}")
            self.dataset_context_widget.setVisible(True)
    
    def update_active_history_card(self):
        """Highlight the currently active history card"""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            widget = self.history_list.itemWidget(item)
            if widget:
                dataset_id = widget.property("datasetId")
                if dataset_id == self.current_dataset_id:
                    # Add active class
                    widget.setProperty("active", True)
                else:
                    # Remove active class
                    widget.setProperty("active", False)
                # Force style refresh
                widget.style().unpolish(widget)
                widget.style().polish(widget)
    
    def update_summary_display(self, data):
        """Update summary cards and charts with data"""
        if not data:
            return
        
        # Extract summary and raw data from nested structure
        summary = data.get('summary', data)
        raw_data = data.get('raw_data', [])
        
        # Update card values using cleaner iteration pattern
        card_mappings = [
            (self.card_total, "total_equipment_count", lambda v: str(v)),
            (self.card_flowrate, "avg_flowrate", lambda v: f"{v:.2f}"),
            (self.card_pressure, "avg_pressure", lambda v: f"{v:.2f}"),
            (self.card_temperature, "avg_temperature", lambda v: f"{v:.2f}")
        ]
        
        for card, key, formatter in card_mappings:
            value_label = card.findChild(QLabel, "statValue")
            if value_label:
                value = summary.get(key, 0)
                value_label.setText(formatter(value))
        
        # Render charts using existing plots module
        self.render_charts(summary, raw_data)
        
        # Show summary and charts
        self.summary_cards_widget.setVisible(True)
        self.charts_widget.setVisible(True)

    def _parse_csv_bytes(self, csv_bytes):
        """Parse CSV bytes into list of dicts for chart rendering"""
        try:
            decoded = csv_bytes.decode("utf-8-sig", errors="replace")
            reader = csv.DictReader(io.StringIO(decoded), skipinitialspace=True)
            normalized_rows = []
            for row in reader:
                if not row:
                    continue
                normalized = {}
                for key, value in row.items():
                    if key is None:
                        continue
                    clean_key = str(key).strip()
                    normalized[clean_key] = value
                if normalized:
                    normalized_rows.append(normalized)
            return normalized_rows
        except Exception:
            return []
    
    def render_charts(self, summary, raw_data):
        """
        Render charts in a scrollable vertical stack
        Scatter, Pie, Flowrate Trend, Bar Comparison
        """
        # Clear existing charts
        while self.charts_container.count():
            item = self.charts_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        def _style_chart(canvas, min_h=420, min_w=None):
            canvas.setParent(self)
            canvas.setObjectName("chartWidget")
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # FIX 1
            canvas.setMinimumHeight(min_h)
            if min_w:
                canvas.setMinimumWidth(min_w)

        # Chart 1: Temperature vs Pressure Scatter
        scatter_chart = create_scatter_plot(raw_data or [])
        _style_chart(scatter_chart, min_h=420)
        self.charts_container.addWidget(scatter_chart)

        # Chart 2: Equipment Distribution Pie
        equipment_dist = summary.get('equipment_type_distribution', {})
        if equipment_dist:
            pie_chart = create_pie_chart(equipment_dist, parent=self)
            _style_chart(pie_chart, min_h=520)
            self.charts_container.addWidget(pie_chart)

        # Chart 3: Flowrate Trend (wide)
        trend_chart = create_flowrate_trend(raw_data or [])
        _style_chart(trend_chart, min_h=420, min_w=1300)
        self.charts_container.addWidget(trend_chart)

        # Chart 4: Multi-Parameter Bar (wide)
        bar_chart = create_bar_chart(raw_data or [])
        _style_chart(bar_chart, min_h=420, min_w=1300)
        self.charts_container.addWidget(bar_chart)
    
    # ===== User Actions =====
    
    def select_file(self):
        """Open file dialog to select CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            import os
            self.file_label.setText(os.path.basename(file_path))
            self.btn_upload.setEnabled(True)
    
    def handle_upload(self):
        """Upload CSV file in background thread"""
        if not self.selected_file_path:
            return
        
        import os
        dataset_name = os.path.basename(self.selected_file_path)
        
        self.btn_upload.setEnabled(False)
        self.upload_progress.setVisible(True)
        self.upload_progress.setValue(0)
        
        thread = UploadThread(self.api_client, self.selected_file_path, dataset_name)
        thread.finished.connect(self.on_upload_complete)
        thread.error.connect(self.on_upload_error)
        thread.progress.connect(self.upload_progress.setValue)
        thread.start()
        
        self.active_threads.append(thread)
    
    def on_upload_complete(self, data):
        """Handle successful upload"""
        self.upload_progress.setVisible(False)
        self.btn_upload.setEnabled(True)
        
        QMessageBox.information(self, "Success", "Dataset uploaded and analyzed successfully!")
        
        # Reload history and latest data
        self.load_history()
        
        # Clear selection
        self.selected_file_path = None
        self.file_label.setText("No file selected")
    
    def on_upload_error(self, error_msg):
        """Handle upload error"""
        self.upload_progress.setVisible(False)
        self.btn_upload.setEnabled(True)
        
        QMessageBox.critical(self, "Upload Error", error_msg)
    
    def handle_export_csv(self):
        """Export current dataset as CSV"""
        if not self.current_dataset_id:
            return
        
        self.export_dataset(self.current_dataset_id, "csv")
    
    def handle_export_pdf(self):
        """Export current dataset as PDF"""
        if not self.current_dataset_id:
            return
        
        self.export_dataset(self.current_dataset_id, "pdf")
    
    def handle_view_raw_data(self):
        """Open raw data table viewer in separate window"""
        if not self.current_dataset_id:
            return
        
        # Get current dataset info
        dataset = None
        for item in self.history_data:
            if item.get('id') == self.current_dataset_id:
                dataset = item
                break
        
        if not dataset:
            QMessageBox.warning(self, "Error", "Dataset not found")
            return
        
        # Fetch raw data
        try:
            result = self.api_client.export_csv(self.current_dataset_id)
            if result.get('success') and result.get('data'):
                raw_data = self._parse_csv_bytes(result.get('data'))
                
                if not raw_data:
                    QMessageBox.warning(self, "No Data", "No raw data available for this dataset")
                    return
                
                # Open table dialog
                dialog = DataTableDialog(
                    dataset_name=dataset.get('name', 'Unknown'),
                    dataset_id=self.current_dataset_id,
                    raw_data=raw_data,
                    parent=self
                )
                dialog.show()
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch raw data")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data:\n{str(e)}")
    
    def export_dataset(self, dataset_id, export_type):
        """Export dataset in background thread"""
        # Select save location
        if export_type == "csv":
            file_filter = "CSV Files (*.csv)"
            default_ext = ".csv"
        else:
            file_filter = "PDF Files (*.pdf)"
            default_ext = ".pdf"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {export_type.upper()}",
            f"dataset_{dataset_id}{default_ext}",
            file_filter
        )
        
        if not save_path:
            return
        
        thread = ExportThread(self.api_client, dataset_id, export_type)
        thread.finished.connect(lambda data: self.on_export_complete(data, save_path))
        thread.error.connect(self.on_error)
        thread.start()
        
        self.active_threads.append(thread)
    
    def on_export_complete(self, data, save_path):
        """Handle successful export"""
        try:
            with open(save_path, "wb") as f:
                f.write(data)
            
            QMessageBox.information(self, "Success", f"File saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")
    
    def on_history_item_clicked(self, item):
        """Handle history list item click"""
        # Already handled by button clicks in custom widget
        pass
    
    def handle_logout(self):
        """Logout and return to login screen"""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_manager.clear_tokens()
            self.close()
            
            # Emit signal or restart login (handled in main.py)
            from ui.login import LoginDialog
            login = LoginDialog(self.api_client, self.auth_manager)
            if login.exec_() == 1:  # Successful login
                # Would need to recreate dashboard - better handled in main.py
                pass
    
    def on_error(self, error_msg):
        """Handle generic error"""
        QMessageBox.warning(self, "Error", error_msg)
    
    def apply_styling(self):
        """Apply QSS styling matching React App.css"""
        self.setStyleSheet("""
            /* Central widget (main app background) */
            #centralWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0F2027,
                    stop:0.5 #203A43,
                    stop:1 #2C5364
                );
            }

            /* Dashboard Header */
            #dashboardHeader {
                background: rgba(15, 32, 39, 0.95);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 16px 24px;
                min-height: 72px;
            }
            
            #headerTitle {
                font-size: 24px;
                font-weight: 700;
                color: #FFFFFF;
                line-height: 1.2;
                letter-spacing: 0.3px;
            }
            
            #headerSubtitle {
                font-size: 14px;
                color: #90A4AE;
                margin-top: 2px;
                line-height: 1.2;
            }
            
            /* Buttons */
            QPushButton {
                font-weight: 600;
                border-radius: 10px;
                padding: 10px 20px;
            }
            
            #btnSecondary {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
            
            #btnSecondary:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: #4FC3F7;
            }
            
            #btnSecondary:disabled {
                background: rgba(255, 255, 255, 0.03);
                color: #546E7A;
                border-color: rgba(255, 255, 255, 0.05);
            }
            
            #btnLogout {
                background: rgba(244, 67, 54, 0.15);
                border: 1px solid rgba(244, 67, 54, 0.3);
                color: #EF5350;
            }
            
            #btnLogout:hover {
                background: rgba(244, 67, 54, 0.25);
                border-color: #EF5350;
            }
            
            #btnUpload {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #66BB6A, stop:1 #43A047
                );
                border: none;
                color: white;
                font-size: 15px;
                padding: 12px 32px;
            }
            
            #btnUpload:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #43A047, stop:1 #66BB6A
                );
            }
            
            #btnUpload:disabled {
                background: #546E7A;
            }
            
            /* Small buttons (history cards) */
            #btnSmallPrimary {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4FC3F7, stop:1 #29B6F6
                );
                border: 1px solid rgba(79, 195, 247, 0.5);
                color: white;
                padding: 8px 16px;
                font-size: 13px;
            }
            
            #btnSmallPrimary:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #29B6F6, stop:1 #4FC3F7
                );
            }
            
            #btnSmallSecondary {
                background: rgba(79, 195, 247, 0.15);
                border: 1px solid rgba(79, 195, 247, 0.3);
                color: #4FC3F7;
                padding: 8px 16px;
                font-size: 13px;
            }
            
            #btnSmallSecondary:hover {
                background: rgba(79, 195, 247, 0.25);
                border-color: rgba(79, 195, 247, 0.5);
            }
            
            /* Sections */
            #uploadSection, #chartsSection {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 14px;
            }
            
            /* Dataset Context Banner */
            #datasetContext {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(79, 195, 247, 0.2),
                    stop:1 rgba(41, 182, 246, 0.15)
                );
                border: 1px solid rgba(79, 195, 247, 0.4);
                border-left: 3px solid #4FC3F7;
                border-radius: 8px;
                padding: 6px 10px;
            }
            
            #datasetContextName {
                font-size: 13px;
                font-weight: 600;
                color: #FFFFFF;
            }
            
            #datasetContextTimestamp {
                font-size: 11px;
                color: #B0BEC5;
            }
            
            #activeBadge {
                font-size: 10px;
                font-weight: 700;
                color: #66BB6A;
                letter-spacing: 0.5px;
                padding: 4px 8px;
                background: rgba(102, 187, 106, 0.15);
                border: 1px solid rgba(102, 187, 106, 0.3);
                border-radius: 14px;
            }
            
            #sectionTitle {
                font-size: 20px;
                font-weight: bold;
                color: #FFFFFF;
                margin-bottom: 12px;
            }
            
            #fileLabel {
                color: #B0BEC5;
                font-size: 14px;
                padding: 8px;
            }
            
            /* Progress bar */
            #uploadProgress {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            
            #uploadProgress::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4FC3F7, stop:1 #29B6F6
                );
                border-radius: 4px;
            }
            
            /* Stat Cards */
            #statCard {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                min-width: 180px;
            }
            
            #statCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(79, 195, 247, 0.5);
                border-width: 2px;
            }
            
            #statLabel {
                color: #90A4AE;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            #statValue {
                font-size: 32px;
                font-weight: bold;
                color: #FFFFFF;
            }
            
            /* History Section (Sidebar) */
            #historySection {
                background: transparent;
                padding: 0px;
            }
            
            #historySectionTitle {
                font-size: 20px;
                font-weight: bold;
                color: #4FC3F7;
                margin-bottom: 8px;
            }
            
            #historySubtitle {
                font-size: 13px;
                color: #90A4AE;
                margin-bottom: 16px;
            }
            
            #historyList {
                background: transparent;
                border: none;
                outline: none;
            }
            
            #historyList::item {
                background: transparent;
                border: none;
            }
            
            #historyCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
            
            #historyCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(79, 195, 247, 0.5);
                border-width: 2px;
            }
            
            /* Active history card highlighting */
            #historyCard[active="true"] {
                background: rgba(79, 195, 247, 0.15);
                border: 2px solid rgba(79, 195, 247, 0.8);
                border-left: 4px solid #4FC3F7;
            }
            
            #historyCardTitle {
                font-size: 16px;
                font-weight: 600;
                color: #E0E0E0;
            }
            
            #historyCardDate {
                font-size: 13px;
                color: #90A4AE;
            }
            
            #historyStatLabel {
                font-size: 12px;
                color: #90A4AE;
                font-weight: 500;
            }
            
            #historyStatValue {
                font-size: 16px;
                color: #4FC3F7;
                font-weight: 600;
            }
            
            /* Chart placeholder */
            #chartPlaceholder {
                background: rgba(255, 255, 255, 0.03);
                border: 2px dashed rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: #90A4AE;
                font-size: 14px;
            }
            
            /* Scroll area and content */
            #scrollArea, #contentWidget {
                border: none;
                background: transparent;
            }
            
            QScrollArea {
                border: none;
                background: transparent;
            }
            
            QSplitter::handle {
                background: rgba(79, 195, 247, 0.2);
                width: 1px;
            }
            
            /* Left Panel */
            #leftPanel {
                background: rgba(15, 32, 39, 0.7);
                border-right: 1px solid rgba(79, 195, 247, 0.2);
            }
            
            #rightPanel {
                background: transparent;
            }
            
            /* Chart Widgets */
            #chartWidget {
                background: rgba(15, 32, 39, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 12px;
            }
            
            #chartTitle {
                font-size: 16px;
                font-weight: 600;
                color: #4FC3F7;
                margin-bottom: 12px;
            }
            
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(79, 195, 247, 0.3);
                border-radius: 5px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(79, 195, 247, 0.5);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def closeEvent(self, event):
        """Clean up threads on close"""
        for thread in self.active_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait()
        
        event.accept()
