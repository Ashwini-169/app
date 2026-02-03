"""
Professional Raw Data Table View
Separate window for data inspection and verification
Industry-standard dark theme with sorting, filtering, and export
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QLineEdit, QLabel, QHeaderView, QAbstractItemView, QMessageBox,
    QFileDialog, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QSortFilterProxyModel
from PyQt5.QtGui import QColor, QFont
import csv


class DataTableModel(QAbstractTableModel):
    """
    Custom table model for raw equipment data
    Implements proper Qt MVC pattern for performance
    """
    
    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data or []
        self._headers = headers or []
        self._original_data = self._data.copy()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers) if self._headers else 0
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data) or col >= len(self._headers):
            return QVariant()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            header = self._headers[col]
            return str(self._data[row].get(header, ''))
        
        elif role == Qt.TextAlignmentRole:
            # Numeric columns right-aligned
            if self._headers[col] in ['Flowrate', 'Pressure', 'Temperature']:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.BackgroundRole:
            # Subtle zebra striping for readability
            if row % 2 == 0:
                return QColor('#1A2530')
            return QColor('#0F2027')
        
        elif role == Qt.ForegroundRole:
            return QColor('#E0E0E0')
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self._headers):
                    # Add units to column headers
                    header = self._headers[section]
                    if header == 'Flowrate':
                        return 'Flowrate (L/min)'
                    elif header == 'Pressure':
                        return 'Pressure (psi)'
                    elif header == 'Temperature':
                        return 'Temperature (°F)'
                    return header
            else:
                return str(section + 1)
        
        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            return font
        
        elif role == Qt.BackgroundRole:
            return QColor('#203A43')
        
        elif role == Qt.ForegroundRole:
            return QColor('#4FC3F7')
        
        return QVariant()
    
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def update_data(self, data, headers):
        """Update table data dynamically"""
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self._original_data = data.copy()
        self.endResetModel()
    
    def get_row_data(self, row):
        """Get full row data as dict"""
        if 0 <= row < len(self._data):
            return self._data[row]
        return {}


class DataTableDialog(QDialog):
    """
    Professional data table viewer in separate window
    Features: sorting, filtering, pagination, export
    """
    
    def __init__(self, dataset_name, dataset_id, raw_data, parent=None):
        super().__init__(parent)
        self.dataset_name = dataset_name
        self.dataset_id = dataset_id
        self.raw_data = raw_data
        self.filtered_data = raw_data.copy()
        
        self.setWindowTitle(f"Raw Data Viewer - {dataset_name}")
        self.setModal(False)  # Allow interaction with main window
        self.resize(1200, 700)
        
        self.init_ui()
        self.apply_styling()
    
    def init_ui(self):
        """Build table UI with controls"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header section
        header_layout = QHBoxLayout()
        
        title = QLabel(f"📊 {self.dataset_name}")
        title.setObjectName("tableTitle")
        header_layout.addWidget(title)
        
        info_label = QLabel(f"Total Records: {len(self.raw_data)}")
        info_label.setObjectName("infoLabel")
        header_layout.addWidget(info_label)
        
        header_layout.addStretch()
        
        # Export button
        btn_export = QPushButton("📥 Export to CSV")
        btn_export.setObjectName("btnExport")
        btn_export.clicked.connect(self.export_to_csv)
        header_layout.addWidget(btn_export)
        
        # Close button
        btn_close = QPushButton("✖ Close")
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.close)
        header_layout.addWidget(btn_close)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        filter_label = QLabel("🔍 Filter:")
        filter_label.setObjectName("filterLabel")
        filter_layout.addWidget(filter_label)
        
        self.filter_column = QComboBox()
        self.filter_column.setObjectName("filterCombo")
        self.filter_column.addItem("All Columns")
        if self.raw_data:
            for header in self.raw_data[0].keys():
                self.filter_column.addItem(header)
        filter_layout.addWidget(self.filter_column)
        
        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("filterInput")
        self.filter_input.setPlaceholderText("Type to filter...")
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input, 1)
        
        btn_clear_filter = QPushButton("Clear")
        btn_clear_filter.setObjectName("btnClearFilter")
        btn_clear_filter.clicked.connect(self.clear_filter)
        filter_layout.addWidget(btn_clear_filter)
        
        filter_layout.addStretch()
        
        # Pagination controls
        page_label = QLabel("Rows per page:")
        page_label.setObjectName("pageLabel")
        filter_layout.addWidget(page_label)
        
        self.rows_per_page = QSpinBox()
        self.rows_per_page.setObjectName("rowsPerPage")
        self.rows_per_page.setMinimum(10)
        self.rows_per_page.setMaximum(1000)
        self.rows_per_page.setSingleStep(10)
        self.rows_per_page.setValue(100)
        self.rows_per_page.valueChanged.connect(self.update_table)
        filter_layout.addWidget(self.rows_per_page)
        
        layout.addLayout(filter_layout)
        
        # Table view
        self.table_view = QTableView()
        self.table_view.setObjectName("dataTableView")
        
        # Extract headers and data
        if self.raw_data:
            headers = list(self.raw_data[0].keys())
        else:
            headers = []
        
        # Create model
        self.model = DataTableModel(self.filtered_data, headers)
        
        # Create proxy model for sorting
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)
        
        self.table_view.setModel(self.proxy_model)
        
        # Table settings
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(False)  # Custom colors in model
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.verticalHeader().setVisible(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # Auto-resize columns initially
        self.table_view.resizeColumnsToContents()
        
        layout.addWidget(self.table_view)
        
        # Status bar
        self.status_label = QLabel(f"Showing {len(self.filtered_data)} of {len(self.raw_data)} records")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)
    
    def apply_filter(self):
        """Filter table data based on search input"""
        filter_text = self.filter_input.text().lower()
        selected_column = self.filter_column.currentText()
        
        if not filter_text:
            self.filtered_data = self.raw_data.copy()
        else:
            self.filtered_data = []
            for row in self.raw_data:
                if selected_column == "All Columns":
                    # Search across all columns
                    if any(filter_text in str(value).lower() for value in row.values()):
                        self.filtered_data.append(row)
                else:
                    # Search in specific column
                    if filter_text in str(row.get(selected_column, '')).lower():
                        self.filtered_data.append(row)
        
        self.update_table()
    
    def clear_filter(self):
        """Clear all filters"""
        self.filter_input.clear()
        self.filter_column.setCurrentIndex(0)
        self.filtered_data = self.raw_data.copy()
        self.update_table()
    
    def update_table(self):
        """Update table model with filtered data"""
        if self.raw_data:
            headers = list(self.raw_data[0].keys())
        else:
            headers = []
        
        # Apply pagination limit
        max_rows = self.rows_per_page.value()
        display_data = self.filtered_data[:max_rows]
        
        self.model.update_data(display_data, headers)
        self.table_view.resizeColumnsToContents()
        
        # Update status
        total = len(self.raw_data)
        filtered = len(self.filtered_data)
        showing = len(display_data)
        
        if filtered < total:
            self.status_label.setText(f"Showing {showing} of {filtered} filtered records (Total: {total})")
        else:
            self.status_label.setText(f"Showing {showing} of {total} records")
    
    def export_to_csv(self):
        """Export current filtered data to CSV"""
        if not self.filtered_data:
            QMessageBox.warning(self, "No Data", "No data to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"{self.dataset_name}_data.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if self.filtered_data:
                    headers = list(self.filtered_data[0].keys())
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(self.filtered_data)
            
            QMessageBox.information(self, "Success", f"Data exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")
    
    def apply_styling(self):
        """Apply dark theme styling matching dashboard"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0F2027,
                    stop:0.5 #203A43,
                    stop:1 #2C5364
                );
            }
            
            #tableTitle {
                font-size: 22px;
                font-weight: bold;
                color: #FFFFFF;
            }
            
            #infoLabel, #statusLabel {
                font-size: 13px;
                color: #B0BEC5;
            }
            
            #filterLabel, #pageLabel {
                font-size: 13px;
                color: #90A4AE;
                font-weight: 600;
            }
            
            #filterInput {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 8px 12px;
                color: #E0E0E0;
                font-size: 13px;
            }
            
            #filterInput:focus {
                border-color: #4FC3F7;
                background: rgba(255, 255, 255, 0.12);
            }
            
            #filterCombo, #rowsPerPage {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px 10px;
                color: #E0E0E0;
                font-size: 13px;
            }
            
            #filterCombo::drop-down, #rowsPerPage::up-button, #rowsPerPage::down-button {
                border: none;
            }
            
            QPushButton {
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
            }
            
            #btnExport {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4FC3F7, stop:1 #29B6F6
                );
                border: 1px solid rgba(79, 195, 247, 0.5);
                color: white;
            }
            
            #btnExport:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #29B6F6, stop:1 #4FC3F7
                );
            }
            
            #btnClose, #btnClearFilter {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
            
            #btnClose:hover, #btnClearFilter:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: #4FC3F7;
            }
            
            #dataTableView {
                background: rgba(15, 32, 39, 0.8);
                border: 1px solid rgba(79, 195, 247, 0.3);
                border-radius: 8px;
                gridline-color: rgba(79, 195, 247, 0.15);
                selection-background-color: rgba(79, 195, 247, 0.3);
                selection-color: #FFFFFF;
            }
            
            QHeaderView::section {
                background: #203A43;
                color: #4FC3F7;
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(79, 195, 247, 0.2);
                border-bottom: 2px solid rgba(79, 195, 247, 0.5);
                font-weight: bold;
                font-size: 11px;
            }
            
            QHeaderView::section:hover {
                background: rgba(79, 195, 247, 0.15);
            }
            
            QTableView::item {
                padding: 6px;
                border: none;
            }
            
            QTableView::item:selected {
                background: rgba(79, 195, 247, 0.25);
                color: #FFFFFF;
            }
            
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(79, 195, 247, 0.4);
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(79, 195, 247, 0.6);
            }
            
            QScrollBar:horizontal {
                background: rgba(255, 255, 255, 0.05);
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(79, 195, 247, 0.4);
                border-radius: 6px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(79, 195, 247, 0.6);
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
        """)
