"""
API client for the Nottorney backend
Handles all HTTP requests to your API
UPDATED: Added notifications endpoint support
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
        self._refreshing_token = False  # Prevent infinite refresh loops
    
    def _get_headers(self, include_auth=False):
        """Get request headers"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if include_auth:
            # Check if token is expired and refresh if needed
            # Prevent infinite loop with flag
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
            # Re-raise authentication errors
            raise
        
        # Debug logging
        print(f"=== API Request ===")
        print(f"Method: {method}")
        print(f"URL: {url}")
        if data:
            # Don't log passwords
            safe_data = data.copy()
            if 'password' in safe_data:
                safe_data['password'] = '***'
            print(f"Request data: {safe_data}")
        print(f"==================")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"=== API Response ===")
            print(f"Status: {response.status_code}")
            
            # Handle different status codes
            if response.status_code == 401:
                # Unauthorized - token invalid
                print("401 Unauthorized - clearing tokens")
                config.clear_tokens()
                raise NottorneyAPIError("Authentication failed. Please login again.")
            
            # Try to parse JSON response
            try:
                result = response.json()
                print(f"Response data: {result}")
                print(f"===================")
            except ValueError:
                # Not JSON response
                print(f"Non-JSON response: {response.text[:200]}")
                print(f"===================")
                if response.status_code >= 400:
                    raise NottorneyAPIError(f"HTTP Error {response.status_code}: {response.text[:200]}")
                result = {"success": True, "data": response.text}
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = result.get('error') or result.get('message') or f"HTTP Error {response.status_code}"
                print(f"Error response: {error_msg}")
                raise NottorneyAPIError(error_msg)
            
            return result
        
        except requests.exceptions.Timeout:
            print("Request timeout")
            raise NottorneyAPIError("Request timed out. Please check your internet connection.")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            raise NottorneyAPIError("Connection error. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            raise NottorneyAPIError(f"Network error: {str(e)}")
    
    # Authentication endpoints
    def login(self, email: str, password: str) -> Dict:
        """
        Login to the Nottorney API
        Returns: { "success": true, "user": {...}, "access_token": "...", "refresh_token": "...", "expires_at": ... }
        """
        if not email or not password:
            raise NottorneyAPIError("Email and password are required")
        
        data = {
            'email': email,
            'password': password
        }
        
        result = self._make_request('POST', '/addon-login', data)
        
        if result.get('success'):
            # Validate response structure
            if not all(k in result for k in ['access_token', 'refresh_token', 'expires_at', 'user']):
                raise NottorneyAPIError("Invalid login response from server")
            
            # Save tokens to config
            config.save_tokens(
                result['access_token'],
                result['refresh_token'],
                result['expires_at']
            )
            config.save_user(result['user'])
            print(f"Login successful, token expires at: {result['expires_at']}")
        else:
            raise NottorneyAPIError(result.get('error', 'Login failed'))
        
        return result
    
    def refresh_token(self) -> Dict:
        """
        Refresh the access token using the refresh token
        Returns: { "success": true, "access_token": "...", "refresh_token": "...", "expires_at": ... }
        """
        refresh_token = config.get_refresh_token()
        if not refresh_token:
            raise NottorneyAPIError("No refresh token available")
        
        data = {
            'refresh_token': refresh_token
        }
        
        print(f"Attempting to refresh token...")
        
        # Don't use include_auth=True here to avoid recursion
        result = self._make_request('POST', '/addon-refresh-token', data, include_auth=False)
        
        if result.get('success'):
            # Validate response structure
            if not all(k in result for k in ['access_token', 'refresh_token', 'expires_at']):
                raise NottorneyAPIError("Invalid refresh response from server")
            
            # Save new tokens
            config.save_tokens(
                result['access_token'],
                result['refresh_token'],
                result['expires_at']
            )
            print(f"Token refreshed successfully, expires at: {result['expires_at']}")
        else:
            raise NottorneyAPIError(result.get('error', 'Token refresh failed'))
        
        return result
    
    # Deck endpoints
    def get_purchased_decks(self) -> List[Dict]:
        """
        Get list of decks purchased by the user
        Returns: { "success": true, "decks": [...], "total_count": 5 }
        """
        result = self._make_request('GET', '/addon-get-purchases', include_auth=True)
        
        if result.get('success'):
            decks = result.get('decks', [])
            print(f"Retrieved {len(decks)} decks")
            
            # Validate and log deck structure
            for i, deck in enumerate(decks):
                print(f"Deck {i+1} fields: {list(deck.keys())}")
                if 'deck_id' not in deck and 'id' not in deck:
                    print(f"Warning: Deck {i+1} missing ID field")
            
            return decks
        
        raise NottorneyAPIError(result.get('error', 'Failed to get purchased decks'))
    
    def check_updates(self) -> Dict:
        """
        Check for updates on all purchased decks
        Returns: {
            "success": true,
            "decks": [{
                "deck_id": "uuid",
                "title": "Deck Name",
                "current_version": "2.0",
                "synced_version": "1.0",
                "has_update": true,
                ...
            }],
            "updates_available": 3,
            "total_decks": 11
        }
        """
        result = self._make_request('POST', '/addon-check-updates', data={}, include_auth=True)
        
        if result.get('success'):
            updates_count = result.get('updates_available', 0)
            total = result.get('total_decks', 0)
            print(f"Update check: {updates_count} updates available out of {total} decks")
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to check for updates'))
    
    def download_deck(self, deck_id: str, version: Optional[str] = None) -> Dict:
        """
        Get download URL for a deck
        Returns: { "success": true, "download_url": "...", "title": "...", "version": "...", "expires_at": ... }
        """
        if not deck_id:
            raise NottorneyAPIError("deck_id is required")
        
        data = {
            'deck_id': deck_id
        }
        
        # Only include version if explicitly provided
        if version:
            data['version'] = version
            print(f"Requesting download for deck_id: {deck_id}, version: {version}")
        else:
            print(f"Requesting download for deck_id: {deck_id} (latest version)")
        
        result = self._make_request('POST', '/addon-download-deck', data, include_auth=True)
        
        if result.get('success'):
            # Validate response
            if 'download_url' not in result:
                raise NottorneyAPIError("No download URL in response")
            
            # Log what we received
            print(f"Download URL obtained for version: {result.get('version', 'unknown')}")
            
            return result
        
        # Enhanced error message
        error_msg = result.get('error', 'Failed to get download URL')
        if 'version' in error_msg.lower():
            error_msg += f"\n\nRequested: deck_id={deck_id}, version={version or 'latest'}"
        
        raise NottorneyAPIError(error_msg)
    
    def download_deck_file(self, download_url: str) -> bytes:
        """
        Download the actual deck file from the download URL
        Returns: The deck file content as bytes
        """
        try:
            print(f"Downloading deck file...")
            print(f"URL: {download_url[:100]}...")
            
            response = requests.get(download_url, timeout=120, stream=True)
            response.raise_for_status()
            
            # Read in chunks to handle large files
            content = b''
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    chunk_count += 1
                    if chunk_count % 100 == 0:  # Log every 100 chunks
                        print(f"Downloaded {len(content)} bytes...")
            
            print(f"Download complete: {len(content)} bytes total")
            return content
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error during download: {e}")
            raise NottorneyAPIError(f"Failed to download deck file: HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request error during download: {e}")
            raise NottorneyAPIError(f"Failed to download deck file: {str(e)}")
    
    # Progress sync endpoint
    def sync_progress(self, progress_data: List[Dict]) -> Dict:
        """
        Sync study progress to the server
        progress_data: [{ "deck_id": "...", "total_cards_studied": 100, ... }]
        Returns: { "success": true, "synced_count": 3 }
        """
        if not progress_data:
            return {"success": True, "synced_count": 0}
        
        data = {
            'progress': progress_data
        }
        
        print(f"Syncing progress for {len(progress_data)} deck(s)")
        
        result = self._make_request('POST', '/addon-sync-progress', data, include_auth=True)
        
        if result.get('success'):
            print(f"Progress synced: {result.get('synced_count', 0)} deck(s)")
            return result
        
        # Don't raise error if progress sync is disabled
        error = result.get('error', '').lower()
        if 'not enabled' in error or 'disabled' in error:
            print("Progress sync not enabled for this user")
            return {"success": False, "synced_count": 0}
        
        raise NottorneyAPIError(result.get('error', 'Failed to sync progress'))
    
    # NEW: Notifications endpoint
    def check_notifications(self, mark_as_read: bool = False, limit: int = 10) -> Dict:
        """
        Check for unread notifications
        
        Args:
            mark_as_read: If True, mark returned notifications as read
            limit: Maximum number of notifications to return (default: 10)
        
        Returns: {
            "success": true,
            "notifications": [{
                "id": "uuid",
                "type": "deck_update" | "announcement",
                "title": "Notification Title",
                "message": "Notification message",
                "created_at": "ISO 8601 timestamp",
                "read": false,
                "metadata": {...}
            }],
            "unread_count": 5,
            "total_count": 20
        }
        """
        data = {
            'mark_as_read': mark_as_read,
            'limit': limit
        }
        
        print(f"Checking notifications (limit={limit}, mark_as_read={mark_as_read})")
        
        result = self._make_request('POST', '/addon-check-notifications', data, include_auth=True)
        
        if result.get('success'):
            notifications = result.get('notifications', [])
            unread_count = result.get('unread_count', 0)
            print(f"Retrieved {len(notifications)} notification(s), {unread_count} unread")
            return result
        
        raise NottorneyAPIError(result.get('error', 'Failed to check notifications'))


# Global API client instance
api = NottorneyAPI()