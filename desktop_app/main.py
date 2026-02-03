"""
Chemical Equipment Parameter Visualizer - Desktop Application
Main entry point with login flow and dashboard lifecycle management
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# Enable high DPI scaling BEFORE QApplication is created
import os
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from api import APIClient
from auth import AuthManager
from ui.login import LoginDialog
from ui.dashboard import Dashboard


class Application:
    """Main application controller"""
    
    def __init__(self):
        print(">>> Desktop app starting...")
        
        # Initialize Qt Application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Chemical Equipment Visualizer")
        
        # Set application-wide font
        from PyQt5.QtGui import QFont
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)
        
        # Initialize API client and auth manager
        self.api_client = APIClient()
        self.auth_manager = AuthManager()
        
        # Application state
        self.dashboard = None
        self.current_username = None
        
        # Check if already logged in
        if self.auth_manager.is_authenticated():
            # Try to use existing token
            username = self.auth_manager.get_username()
            access_token = self.auth_manager.get_access_token()
            
            if username and access_token:
                self.api_client.access_token = access_token
                self.current_username = username
                self.show_dashboard()
            else:
                self.show_login()
        else:
            self.show_login()
    
    def show_login(self):
        """Show login dialog"""
        print(">>> Showing login dialog...")
        login_dialog = LoginDialog(self.api_client)
        login_dialog.login_successful.connect(self.on_login_success)
        
        # Show modal dialog
        result = login_dialog.exec_()
        
        if result == 0:  # Dialog rejected (closed without login)
            sys.exit(0)
    
    def on_login_success(self, username, access_token):
        """Handle successful login"""
        print(f">>> Login successful for user: {username}")
        self.current_username = username
        self.api_client.access_token = access_token
        
        # Save tokens to auth manager
        # Note: refresh_token would need to be returned from login for this to work
        self.auth_manager.save_tokens(username, access_token, "")
        
        self.show_dashboard()
    
    def show_dashboard(self):
        """Show main dashboard window"""
        print(">>> Showing dashboard...")
        self.dashboard = Dashboard(
            self.api_client,
            self.auth_manager,
            self.current_username
        )
        
        # Connect dashboard close to logout check
        self.dashboard.destroyed.connect(self.on_dashboard_closed)
        
        self.dashboard.show()
        print(">>> Dashboard displayed")
    
    def on_dashboard_closed(self):
        """Handle dashboard window closure"""
        # Check if user logged out or just closed window
        if not self.auth_manager.is_authenticated():
            # Logged out - show login again
            self.show_login()
        else:
            # Just closed - exit application
            sys.exit(0)
    
    def run(self):
        """Start application event loop"""
        return self.app.exec_()


def main():
    """Application entry point"""
    try:
        app = Application()
        sys.exit(app.run())
    
    except Exception as e:
        # Show error dialog
        error_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected error occurred:\n\n{str(e)}\n\nThe application will now exit."
        )
        
        import traceback
        traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()
