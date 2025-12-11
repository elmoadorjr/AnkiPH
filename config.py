"""
Configuration management for the Nottorney addon
UPDATED: Added notification tracking and last check timestamp
"""

from aqt import mw
from datetime import datetime
import json


class Config:
    """Manages addon configuration and authentication state"""
    
    def __init__(self):
        self.addon_name = "Nottorney_Addon"
        self._config_cache = None
        self._cache_timestamp = 0
        
    def _get_config(self):
        """Get the addon config from Anki with caching"""
        try:
            # Use cache if less than 1 second old
            current_time = datetime.now().timestamp()
            if self._config_cache and (current_time - self._cache_timestamp) < 1:
                return self._config_cache
            
            config = mw.addonManager.getConfig(self.addon_name)
            if config is None:
                print(f"Config is None for {self.addon_name}, using defaults")
                config = self._get_default_config()
            
            # Update cache
            self._config_cache = config
            self._cache_timestamp = current_time
            
            return config
        except Exception as e:
            print(f"Error reading config for {self.addon_name}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Get the default configuration"""
        return {
            "api_url": "https://ladvckxztcleljbiomcf.supabase.co/functions/v1",
            "auto_sync_enabled": True,
            "auto_sync_interval_hours": 1,
            "downloaded_decks": {},
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
            "user": None,
            "ui_mode": "minimal",
            "last_notification_check": None,
            "unread_notification_count": 0
        }
    
    def _save_config(self, data):
        """Save the addon config to Anki"""
        try:
            # Make a deep copy to avoid reference issues
            data_to_save = json.loads(json.dumps(data))
            
            mw.addonManager.writeConfig(self.addon_name, data_to_save)
            
            # Invalidate cache after save
            self._config_cache = None
            self._cache_timestamp = 0
            
            print(f"✓ Config saved successfully")
            return True
        except Exception as e:
            print(f"✗ ERROR: Failed to save config: {e}")
            self._config_cache = None
            self._cache_timestamp = 0
            return False
    
    def _invalidate_cache(self):
        """Invalidate the config cache"""
        self._config_cache = None
        self._cache_timestamp = 0
    
    # === UI MODE ===
    
    def get_ui_mode(self):
        """Get the user's preferred UI mode"""
        mode = self._get_config().get('ui_mode', 'minimal')
        if mode not in ['minimal', 'classic']:
            mode = 'minimal'
        return mode
    
    def set_ui_mode(self, mode):
        """Set the user's preferred UI mode"""
        if mode not in ['minimal', 'classic']:
            mode = 'minimal'
        
        cfg = self._get_config()
        cfg['ui_mode'] = mode
        return self._save_config(cfg)
    
    # === AUTHENTICATION ===
    
    def save_tokens(self, access_token, refresh_token, expires_at):
        """Save authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = access_token
        cfg['refresh_token'] = refresh_token
        cfg['expires_at'] = expires_at
        
        success = self._save_config(cfg)
        if success:
            print(f"Tokens saved: expires_at={expires_at}")
        return success
    
    def get_access_token(self):
        """Get the current access token"""
        return self._get_config().get('access_token')
    
    def get_refresh_token(self):
        """Get the current refresh token"""
        return self._get_config().get('refresh_token')
    
    def get_token_expiry(self):
        """Get the token expiration timestamp"""
        return self._get_config().get('expires_at')
    
    def is_token_expired(self):
        """Check if the access token is expired"""
        expires_at = self.get_token_expiry()
        if not expires_at:
            return True
        
        current_time = datetime.now().timestamp()
        buffer_seconds = 300  # 5 minutes
        return current_time >= (expires_at - buffer_seconds)
    
    def clear_tokens(self):
        """Clear all authentication tokens"""
        cfg = self._get_config()
        cfg['access_token'] = None
        cfg['refresh_token'] = None
        cfg['expires_at'] = None
        cfg['user'] = None
        
        success = self._save_config(cfg)
        if success:
            print("Tokens cleared successfully")
        return success
    
    def is_logged_in(self):
        """Check if user is logged in with a valid token"""
        return bool(self.get_access_token())
    
    # === USER DATA ===
    
    def save_user(self, user_data):
        """Save user information"""
        if not user_data:
            return False
        
        cfg = self._get_config()
        cfg['user'] = user_data
        return self._save_config(cfg)
    
    def get_user(self):
        """Get saved user information"""
        return self._get_config().get('user')
    
    # === API SETTINGS ===
    
    def get_api_url(self):
        """
        Get the API base URL
        Default: Supabase edge functions URL
        """
        url = self._get_config().get('api_url', 
            'https://ladvckxztcleljbiomcf.supabase.co/functions/v1')
        url = url.rstrip('/')
        
        # Validate URL format
        if not url.startswith('http'):
            print(f"⚠ Warning: API URL doesn't start with http: {url}")
        
        return url
    
    # === NOTIFICATIONS ===
    
    def get_last_notification_check(self):
        """Get timestamp of last notification check"""
        return self._get_config().get('last_notification_check')
    
    def update_last_notification_check(self):
        """Update last notification check timestamp to now"""
        cfg = self._get_config()
        cfg['last_notification_check'] = datetime.now().isoformat()
        return self._save_config(cfg)
    
    def get_unread_notification_count(self):
        """Get cached unread notification count"""
        return self._get_config().get('unread_notification_count', 0)
    
    def set_unread_notification_count(self, count):
        """Update cached unread notification count"""
        cfg = self._get_config()
        cfg['unread_notification_count'] = max(0, int(count))
        return self._save_config(cfg)
    
    def should_check_notifications(self, interval_minutes=15):
        """Check if enough time has passed to check notifications again"""
        last_check = self.get_last_notification_check()
        if not last_check:
            return True
        
        try:
            last_check_time = datetime.fromisoformat(last_check)
            time_since_check = (datetime.now() - last_check_time).total_seconds() / 60
            return time_since_check >= interval_minutes
        except (ValueError, TypeError):
            return True
    
    # === DOWNLOADED DECKS TRACKING ===
    
    def save_downloaded_deck(self, deck_id, version, anki_deck_id):
        """
        Track a downloaded deck
        FIXED: Ensures anki_deck_id is stored as integer
        """
        if not deck_id:
            print("✗ Cannot save deck: no deck_id")
            return False
        
        # CRITICAL: Convert anki_deck_id to integer
        try:
            anki_deck_id = int(anki_deck_id)
        except (ValueError, TypeError) as e:
            print(f"✗ Cannot save deck: invalid anki_deck_id {anki_deck_id} ({e})")
            return False
        
        # CRITICAL: Verify the deck exists in Anki before saving
        if not self._verify_deck_exists(anki_deck_id):
            print(f"✗ Cannot save deck: Anki deck {anki_deck_id} does not exist")
            return False
        
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg:
            cfg['downloaded_decks'] = {}
        
        cfg['downloaded_decks'][deck_id] = {
            'version': version,
            'anki_deck_id': anki_deck_id,
            'downloaded_at': datetime.now().isoformat()
        }
        
        success = self._save_config(cfg)
        
        if success:
            print(f"✓ Saved deck: {deck_id} v{version} (Anki ID: {anki_deck_id})")
        else:
            print(f"✗ Failed to save deck: {deck_id}")
        
        return success
    
    def get_downloaded_decks(self):
        """Get dictionary of downloaded decks"""
        # Always get fresh data
        self._invalidate_cache()
        decks = self._get_config().get('downloaded_decks', {})
        result = decks if isinstance(decks, dict) else {}
        print(f"Retrieved {len(result)} tracked deck(s)")
        return result
    
    def is_deck_downloaded(self, deck_id):
        """
        Check if a deck is downloaded AND still exists in Anki
        """
        if not deck_id:
            return False
        
        downloaded_decks = self.get_downloaded_decks()
        if deck_id not in downloaded_decks:
            return False
        
        # Verify the deck still exists in Anki
        anki_deck_id = downloaded_decks[deck_id].get('anki_deck_id')
        if not anki_deck_id:
            return False
        
        # Convert to int if needed
        try:
            anki_deck_id = int(anki_deck_id)
        except (ValueError, TypeError):
            print(f"✗ Invalid anki_deck_id for {deck_id}: {anki_deck_id}")
            return False
        
        return self._verify_deck_exists(anki_deck_id)
    
    def get_deck_version(self, deck_id):
        """Get the version of a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(deck_id, {})
        return deck_info.get('version')
    
    def get_deck_anki_id(self, deck_id):
        """Get the Anki deck ID for a downloaded deck"""
        if not deck_id:
            return None
        
        decks = self.get_downloaded_decks()
        deck_info = decks.get(deck_id, {})
        anki_deck_id = deck_info.get('anki_deck_id')
        
        if anki_deck_id:
            try:
                return int(anki_deck_id)
            except (ValueError, TypeError):
                print(f"✗ Invalid anki_deck_id: {anki_deck_id}")
                return None
        
        return None
    
    def remove_downloaded_deck(self, deck_id):
        """Remove a deck from tracking"""
        if not deck_id:
            print(f"✗ Cannot remove deck: no deck_id")
            return False
        
        print(f"Removing deck from tracking: {deck_id}")
        
        # Get fresh config
        self._invalidate_cache()
        cfg = self._get_config()
        
        if 'downloaded_decks' not in cfg or deck_id not in cfg['downloaded_decks']:
            print(f"✓ Deck {deck_id} not tracked (already removed)")
            return True
        
        # Remove the deck
        del cfg['downloaded_decks'][deck_id]
        
        # Save changes
        success = self._save_config(cfg)
        
        if success:
            print(f"✓ Removed deck: {deck_id}")
            
            # Verify removal
            self._invalidate_cache()
            verification = self._get_config().get('downloaded_decks', {})
            if deck_id in verification:
                print(f"✗ WARNING: Deck {deck_id} still present after removal!")
                return False
        else:
            print(f"✗ Failed to remove deck: {deck_id}")
        
        return success
    
    def _verify_deck_exists(self, anki_deck_id):
        """Verify that a deck exists in Anki's collection"""
        try:
            if not mw or not mw.col:
                print(f"⚠ Cannot verify deck {anki_deck_id}: collection not available")
                return False
            
            # Ensure we're working with an integer
            anki_deck_id = int(anki_deck_id)
            
            # Get the deck by integer ID
            deck = mw.col.decks.get(anki_deck_id)
            exists = deck is not None
            
            if not exists:
                print(f"✗ Deck {anki_deck_id} does not exist in Anki")
            
            return exists
        except (ValueError, TypeError) as e:
            print(f"✗ Invalid deck ID {anki_deck_id}: {e}")
            return False
        except Exception as e:
            print(f"✗ Error verifying deck {anki_deck_id}: {e}")
            return False
    
    def cleanup_deleted_decks(self):
        """
        Remove all deck tracking for decks that no longer exist in Anki
        Returns: (cleaned_count, total_tracked)
        """
        print("\n=== Cleaning up deleted decks ===")
        
        downloaded_decks = self.get_downloaded_decks()
        total_tracked = len(downloaded_decks)
        decks_to_remove = []
        
        print(f"Checking {total_tracked} tracked deck(s)...")
        
        for deck_id, deck_info in downloaded_decks.items():
            anki_deck_id = deck_info.get('anki_deck_id')
            
            if not anki_deck_id:
                print(f"  Deck {deck_id}: No Anki ID → mark for removal")
                decks_to_remove.append(deck_id)
                continue
            
            # Convert to int
            try:
                anki_deck_id = int(anki_deck_id)
            except (ValueError, TypeError):
                print(f"  Deck {deck_id}: Invalid Anki ID {anki_deck_id} → mark for removal")
                decks_to_remove.append(deck_id)
                continue
            
            if not self._verify_deck_exists(anki_deck_id):
                print(f"  Deck {deck_id} (Anki {anki_deck_id}): Not found → mark for removal")
                decks_to_remove.append(deck_id)
            else:
                print(f"  Deck {deck_id} (Anki {anki_deck_id}): ✓ Exists")
        
        # Remove all marked decks
        cleaned_count = 0
        for deck_id in decks_to_remove:
            if self.remove_downloaded_deck(deck_id):
                cleaned_count += 1
        
        print(f"\n=== Cleanup complete: {cleaned_count}/{len(decks_to_remove)} removed ===\n")
        
        return (cleaned_count, total_tracked)


# Global config instance
config = Config()