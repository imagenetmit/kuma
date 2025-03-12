import time
import requests
from typing import Optional, Dict
from .exceptions import NinjaRMMAuthError
from urllib.parse import urlencode

class TokenManager:
    """Manages OAuth2 token lifecycle for NinjaRMM API"""
    
    def __init__(self, token_url: str, client_id: str, client_secret: str, scope: str):
        """
        Initialize the token manager.
        
        Args:
            token_url (str): OAuth2 token endpoint URL
            client_id (str): OAuth2 client ID
            client_secret (str): OAuth2 client secret
            scope (str): OAuth2 scope(s)
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = "monitoring management control"
        
        self._access_token: Optional[str] = None
        self._refresh_token_value: Optional[str] = None
        self._token_expiry: Optional[float] = None

    def _is_token_expired(self) -> bool:
        """
        Check if the current token is expired.
        
        Returns:
            bool: True if token is expired or will expire in next 60 seconds
        """
        if not self._token_expiry:
            return True
        
        # Add 60-second buffer to prevent edge cases
        return time.time() + 60 >= self._token_expiry

    def _get_new_access_token(self) -> str:
        """Get new access token using client credentials flow."""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=payload,  # requests will handle url encoding
                headers=headers
            )
            

            
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data['access_token']
            self._token_expiry = time.time() + token_data['expires_in']
            self._refresh_token_value = token_data.get('refresh_token')
            
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            raise NinjaRMMAuthError(f"Failed to get new access token: {str(e)}")

    def _refresh_token(self) -> str:
        """
        Refresh the access token using refresh token.
        
        Returns:
            str: New access token
            
        Raises:
            NinjaRMMAuthError: If token refresh fails
        """
        if not self._refresh_token_value:
            raise NinjaRMMAuthError("No refresh token available")
            
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token_value,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data['access_token']
            self._token_expiry = time.time() + token_data['expires_in']
            self._refresh_token_value = token_data.get('refresh_token')
            
            return self._access_token
            
        except Exception as e:
            raise NinjaRMMAuthError(f"Failed to refresh token: {str(e)}")

    def get_valid_token(self) -> str:
        """
        Get a valid access token, obtaining or refreshing if necessary.
        
        Returns:
            str: Valid access token
            
        Raises:
            NinjaRMMAuthError: If unable to obtain valid token
        """
        try:
            if not self._access_token or not self._token_expiry:
                # No token exists, get new one
                return self._get_new_access_token()
                
            if self._is_token_expired():
                # Token is expired
                if self._refresh_token_value:
                    try:
                        return self._refresh_token()
                    except NinjaRMMAuthError:
                        # If refresh fails, try getting new token
                        return self._get_new_access_token()
                else:
                    # No refresh token, get new access token
                    return self._get_new_access_token()
                    
            # Token is still valid
            return self._access_token
            
        except Exception as e:
            raise NinjaRMMAuthError(f"Token management failed: {str(e)}") 