"""
API client for the Nottorney backend - FIXED VERSION
Added missing batch_download_decks and get_changelog methods
"""

import requests
from typing import Dict, List, Optional
from .config import config


class NottorneyAPIError(Exception):
    """Custom exception for API errors"""
    pass


class NottorneyAPI:
    """Client for interacting with the Nottorney API"""
    
    def __init__(self):
        self.base_url = config.get_api_url()
        self._refreshing_token = False
    
    def _get_headers(self, include_auth=False):
        """Get request headers"""
        headers = {'Content-Type': 'application/json'}
        
        if include_auth:
            if config.is_token_expired() and not self._refreshing_token:
                try:
                    print("Token expired, attempting refresh...")
                    self._refreshing_token = True
                    result = self.refresh_token()
                    self._refreshing_token = False
                    
                    if not result.get('success'):
                        print("Token refresh failed, clearing tokens")
                        config.clear_tokens()
                        raise NottorneyAPIError("Session expired. Please login again.")
                except Exception as e:
                    self._refreshing_token = False
                    print(f"Token refresh exception: {e}")
                    config.clear_tokens()
                    raise NottorneyAPIError("Session expired. Please login again.")
            
            access_token = config.get_access_token()
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
            else:
                raise NottorneyAPIError("Not authenticated. Please login.")
        
        return headers
    
    def _make_request(self, method, endpoint, data=None, include_auth=False, timeout=30):
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            headers = self._get_headers(include_auth)
        except NottorneyAPIError:
            raise
        
        print(f"=== API Request ===")
        print(f"{method} {url}")
        if data:
            safe_data = data.copy()
            if 'password' in safe_data:
                safe_data['password'] = '***'
            print(f"Data: {safe_data}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 401:
                print("401 Unauthorized - clearing tokens")
                config.clear_tokens()
                raise NottorneyAPIError("Authentication failed. Please login again.")
            
            try:
                result = response.json()
                print(f"Response: {result}")
            except ValueError:
                print(f"Non-JSON response: {response.text[:200]}")
                if response.status_code >= 400:
                    raise NottorneyAPIError(f"HTTP Error {response.status_code}: {response.text[:200]}")
                result = {"success": True, "data": response.text}
            
            if response.status_code >= 400:
                error_msg = result.get('error') or result.get('message') or f"HTTP Error {response.status_code}"
                print(f"Error: {error_msg}")
                raise NottorneyAPIError(error_msg)
            
            return result
        
        except requests.exceptions.Timeout:
            raise NottorneyAPIError("Request timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError as e:
            raise NottorneyAPIError("Connection error. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise NottorneyAPIError(f"Network error: {str(e)}")
    
    def login(self, email: str, password: str) -> Dict:
        """Login to the Nottorney API"""
        if not email or not password:
            raise NottorneyAPIError("Email and password are required")
        
        data = {'email': email, 'password': password}
        result = self._make_request('POST', '/addon-login', data)
        
        if result.get('success'):
            if not all(k in result for k in ['access_token', 'refresh_token', 'expires_at', 'user']):
                raise NottorneyAPIError("Invalid login response from server")
            
            config.save_tokens(result['access_token'], result['refresh_token'], result['expires_at'])
            config.save_user(result['user'])
            print(f"Login successful, token expires at: {result['expires_at']}")
        else:
            raise NottorneyAPIError(result.get('error', 'Login failed'))
        
        return result
    
    def refresh_token(self) -> Dict:
        """Refresh the access token using the refresh token"""
        refresh_token = config.get_refresh_token()
        if not refresh_token:
            raise NottorneyAPIError("No refresh token available")
        
        data = {'refresh_token': refresh_token}
        result = self._make_request('POST', '/addon-refresh-token', data, include_auth=False)
        
        if result.get('success'):
            if not all(k in result for k in ['access_token', 'refresh_token', 'expires_at']):
                raise NottorneyAPIError("Invalid refresh response from server")
            
            config.save_tokens(result['access_token'], result['refresh_token'], result['expires_at'])
            print(f"Token refreshed successfully")
        else:
            raise NottorneyAPIError(result.get('error', 'Token refresh failed'))
        
        return result
    
    def get_purchased_decks(self) -> List[Dict]:
        """Get list of decks purchased by the user"""
        result = self._make_request('POST', '/addon-get-purchases', data={}, include_auth=True)
        
        if result.get('success'):
            decks = result.get('purchases', [])
            print(f"Retrieved {len(decks)} decks")
            return decks
        
        raise NottorneyAPIError(result.get('error', 'Failed to get purchased decks'))
    
    def check_updates(self) -> Dict:
        """Check for updates on all purchased decks"""
        result = self._make_request('POST', '/addon-check-updates', data={}, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to check for updates'))
    
    def download_deck(self, deck_id: str, version: Optional[str] = None) -> Dict:
        """Get download URL for a deck"""
        if not deck_id:
            raise NottorneyAPIError("deck_id is required")
        
        data = {'deck_id': deck_id}
        if version:
            data['version'] = version
        
        result = self._make_request('POST', '/addon-download-deck', data, include_auth=True)
        
        if result.get('success'):
            if 'download_url' not in result:
                raise NottorneyAPIError("No download URL in response")
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to get download URL'))
    
    def batch_download_decks(self, deck_ids: List[str]) -> Dict:
        """
        NEW: Batch download multiple decks (max 10)
        Returns: {"success": true, "downloads": [...], "failed": [...]}
        """
        if not deck_ids:
            raise NottorneyAPIError("deck_ids is required")
        
        if len(deck_ids) > 10:
            raise NottorneyAPIError("Maximum 10 decks per batch request")
        
        data = {'deck_ids': deck_ids}
        print(f"Batch downloading {len(deck_ids)} deck(s)")
        
        result = self._make_request('POST', '/addon-batch-download', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError(result.get('error', 'Batch download failed'))
    
    def get_changelog(self, deck_id: str) -> Dict:
        """
        NEW: Get version history/changelog for a deck
        Returns: {"success": true, "title": "...", "versions": [...]}
        """
        if not deck_id:
            raise NottorneyAPIError("deck_id is required")
        
        data = {'deck_id': deck_id}
        print(f"Fetching changelog for deck: {deck_id}")
        
        result = self._make_request('POST', '/addon-get-changelog', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to get changelog'))
    
    def download_deck_file(self, download_url: str) -> bytes:
        """Download the actual deck file from the download URL"""
        try:
            print(f"Downloading deck file from URL...")
            response = requests.get(download_url, timeout=120, stream=True)
            response.raise_for_status()
            
            content = b''
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    chunk_count += 1
                    if chunk_count % 100 == 0:
                        print(f"Downloaded {len(content)} bytes...")
            
            print(f"Download complete: {len(content)} bytes")
            return content
        except requests.exceptions.HTTPError as e:
            raise NottorneyAPIError(f"Failed to download: HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise NottorneyAPIError(f"Failed to download: {str(e)}")
    
    def sync_progress(self, progress_data: List[Dict]) -> Dict:
        """Sync study progress to the server"""
        if not progress_data:
            return {"success": True, "synced_count": 0}
        
        data = {'progress': progress_data}
        print(f"Syncing progress for {len(progress_data)} deck(s)")
        
        result = self._make_request('POST', '/addon-sync-progress', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        error = result.get('error', '').lower()
        if 'not enabled' in error or 'disabled' in error:
            print("Progress sync not enabled")
            return {"success": False, "synced_count": 0}
        
        raise NottorneyAPIError(result.get('error', 'Failed to sync progress'))
    
    def check_notifications(self, mark_as_read: bool = False, limit: int = 10) -> Dict:
        """Check for unread notifications"""
        data = {'mark_as_read': mark_as_read, 'limit': limit}
        result = self._make_request('POST', '/addon-check-notifications', data, include_auth=True)
        
        if result.get('success'):
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to check notifications'))


# Global API client instance
api = NottorneyAPI()