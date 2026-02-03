"""
Authentication module for desktop app
Manages JWT tokens and login state
"""

from typing import Optional
import json
import os


class AuthManager:
    """Manage authentication state and token persistence"""
    
    def __init__(self, token_file: str = ".token_cache.json"):
        self.token_file = token_file
        self.username: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.load_tokens()
    
    def save_tokens(self, username: str, access_token: str, refresh_token: str):
        """Save tokens to file for persistence"""
        self.username = username
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        try:
            with open(self.token_file, 'w') as f:
                json.dump({
                    "username": username,
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }, f)
        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")
    
    def load_tokens(self) -> bool:
        """Load tokens from file"""
        if not os.path.exists(self.token_file):
            return False
        
        try:
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                self.username = data.get("username")
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                return True
        except Exception as e:
            print(f"Warning: Could not load tokens: {e}")
            return False
    
    def clear_tokens(self):
        """Clear tokens and delete cache file"""
        self.username = None
        self.access_token = None
        self.refresh_token = None
        
        if os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
            except Exception as e:
                print(f"Warning: Could not delete token file: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return bool(self.access_token)
    
    def get_access_token(self) -> str:
        """Get access token"""
        return self.access_token or ""
    
    def get_username(self) -> str:
        """Get stored username"""
        return self.username or ""
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token"""
        return self.access_token
