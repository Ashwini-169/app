"""
Login dialog for desktop app
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from api import APIClient


class LoginDialog(QDialog):
    """Login/Register dialog with JWT authentication"""
    
    login_successful = pyqtSignal(str, str)  # username, access_token
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("Chemical Equipment Visualizer - Login")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.apply_dark_theme()
    
    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Chemical Equipment Visualizer")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        subtitle = QLabel("Desktop Application")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #4FC3F7; font-size: 12px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Tab widget for Login/Register
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_login_tab(), "Login")
        self.tabs.addTab(self.create_register_tab(), "Register")
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def create_login_tab(self) -> QWidget:
        """Create login tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        layout.addWidget(self.login_username)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("Enter password")
        self.login_password.returnPressed.connect(self.handle_login)
        layout.addWidget(self.login_password)
        
        layout.addSpacing(10)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #4FC3F7, stop:1 #29B6F6);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #29B6F6, stop:1 #4FC3F7);
            }
            QPushButton:pressed {
                background: #0288D1;
            }
        """)
        layout.addWidget(login_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_register_tab(self) -> QWidget:
        """Create registration tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choose username")
        layout.addWidget(self.reg_username)
        
        # Email
        layout.addWidget(QLabel("Email (optional):"))
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Enter email")
        layout.addWidget(self.reg_email)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setPlaceholderText("Choose password")
        layout.addWidget(self.reg_password)
        
        # Confirm password
        layout.addWidget(QLabel("Confirm Password:"))
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setPlaceholderText("Confirm password")
        self.reg_confirm.returnPressed.connect(self.handle_register)
        layout.addWidget(self.reg_confirm)
        
        layout.addSpacing(10)
        
        # Register button
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.handle_register)
        register_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #66BB6A, stop:1 #4CAF50);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #4CAF50, stop:1 #66BB6A);
            }
            QPushButton:pressed {
                background: #388E3C;
            }
        """)
        layout.addWidget(register_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def handle_login(self):
        """Handle login button click"""
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password")
            return
        
        # Call API
        result = self.api_client.login(username, password)
        
        if result["success"]:
            QMessageBox.information(self, "Success", "Login successful!")
            self.login_successful.emit(username, result["tokens"]["access"])
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", result["message"])
    
    def handle_register(self):
        """Handle registration button click"""
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text().strip()
        confirm = self.reg_confirm.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Input Error", "Passwords do not match")
            return
        
        # Call API
        result = self.api_client.register(username, password, email)
        
        if result["success"]:
            QMessageBox.information(self, "Success", 
                                   "Registration successful! You can now login.")
            self.tabs.setCurrentIndex(0)  # Switch to login tab
            self.login_username.setText(username)
            self.login_password.setFocus()
        else:
            QMessageBox.critical(self, "Registration Failed", result["message"])
    
    def apply_dark_theme(self):
        """Apply dark theme to dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E293B;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #2C3E50;
                color: #E0E0E0;
                border: 1px solid #4FC3F7;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4FC3F7;
            }
            QTabWidget::pane {
                border: 1px solid #4FC3F7;
                background-color: #1E293B;
            }
            QTabBar::tab {
                background-color: #2C3E50;
                color: #B0BEC5;
                padding: 8px 20px;
                border: 1px solid #4FC3F7;
            }
            QTabBar::tab:selected {
                background-color: #4FC3F7;
                color: white;
            }
        """)
