"""
API Client for Chemical Equipment Visualizer Desktop App
Handles all communication with Django backend
"""

import requests
from typing import Optional, Dict, Any
import json


class APIClient:
    """REST API client with JWT authentication"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with JWT token"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login and obtain JWT tokens
        Returns: {"success": True/False, "message": str, "tokens": {...}}
        """
        url = f"{self.base_url}/api/token/"
        try:
            response = requests.post(
                url,
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access")
                self.refresh_token = data.get("refresh")
                return {
                    "success": True,
                    "message": "Login successful",
                    "tokens": data
                }
            else:
                return {
                    "success": False,
                    "message": f"Login failed: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def register(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        """
        Register a new user
        Returns: {"success": True/False, "message": str}
        """
        url = f"{self.base_url}/api/register/"
        try:
            response = requests.post(
                url,
                json={"username": username, "password": password, "email": email},
                timeout=10
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "message": "Registration successful"
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "message": error_data.get("error", f"Registration failed: {response.status_code}")
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def upload_csv(self, file_path: str, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload CSV file
        Returns: {"success": True/False, "message": str, "data": {...}}
        """
        url = f"{self.base_url}/api/upload/"
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'name': dataset_name or file_path.split('/')[-1]}
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": "File uploaded successfully",
                    "data": response.json()
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "success": False,
                    "message": error_data.get("error", f"Upload failed: {response.status_code}")
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": "File not found"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def get_latest_summary(self) -> Dict[str, Any]:
        """
        Get latest dataset summary and raw data
        Returns: {"success": True/False, "message": str, "data": {...}}
        """
        url = f"{self.base_url}/api/summary/latest/"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Data retrieved",
                    "data": response.json()
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "message": "No datasets found"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to retrieve data: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def get_history(self) -> Dict[str, Any]:
        """
        Get upload history (last 5 datasets)
        Returns: {"success": True/False, "message": str, "data": [...]}
        """
        url = f"{self.base_url}/api/history/"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "History retrieved",
                    "data": response.json().get("history", [])
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to retrieve history: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def export_csv(self, dataset_id: Optional[int] = None, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export dataset as CSV
        Returns: {"success": True/False, "message": str}
        """
        url = f"{self.base_url}/api/export/csv/"
        if dataset_id:
            url += f"{dataset_id}/"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                return {
                    "success": True,
                    "message": "CSV exported successfully",
                    "data": response.content
                }
            else:
                return {
                    "success": False,
                    "message": f"Export failed: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def export_pdf(self, dataset_id: Optional[int] = None, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate and download PDF report
        Returns: {"success": True/False, "message": str}
        """
        url = f"{self.base_url}/api/report/pdf/"
        if dataset_id:
            url += f"{dataset_id}/"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                return {
                    "success": True,
                    "message": "PDF report generated successfully",
                    "data": response.content
                }
            else:
                return {
                    "success": False,
                    "message": f"PDF generation failed: {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def logout(self):
        """Clear stored tokens"""
        self.access_token = None
        self.refresh_token = None
