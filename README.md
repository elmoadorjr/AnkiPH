# Nottorney Anki Addon - Enhanced Edition

**Version:** 1.1.0  
**Updated:** December 15, 2024  
**Compatible with:** Anki 24.x - 25.x (PyQt6)

---

## 🎉 What's New in v1.1.0

This version adds major new features and improvements:

### 🆕 New Features:

1. **Automatic Update Checking**
   - Checks for deck updates in the background
   - Configurable check interval (default: 24 hours)
   - Visual indicators showing which decks have updates
   - One-click update from Updates tab

2. **Modern Tabbed Interface**
   - **My Decks** tab: View your downloaded decks with status indicators
   - **Browse** tab: Discover and download new decks
   - **Updates** tab: See available updates at a glance
   - Clean, organized layout with better usability

3. **Enhanced API Integration**
   - Update checking (`/addon-check-updates`)
   - Changelog viewing (`/addon-get-changelog`)
   - Notifications (`/addon-check-notifications`)
   - Batch download support (up to 10 decks)
   - Full AnkiHub-parity endpoints (ready for Phase 3)

4. **Visual Status Indicators**
   - 🟢 Up to date
   - 🟡 Update available
   - ✓ Downloaded
   - Update badge in toolbar

5. **Better Progress Syncing**
   - Enhanced sync state tracking
   - Last sync timestamp visible
   - Protected fields configuration (backend-ready)

### v1.0.2 Fixes (Still Included):
- ✅ Fixed `browse_decks` action parameter
- ✅ Fixed response format handling
- ✅ Fixed deck field names (`title` vs `name`)

---

## 📦 Installation

### Method 1: Complete Installation (Recommended)

1. **Close Anki completely**

2. **Navigate to your Anki addons folder:**
   - **Windows:** `C:\Users\[YourUsername]\AppData\Roaming\Anki2\addons21\`
   - **Mac:** `~/Library/Application Support/Anki2/addons21/`
   - **Linux:** `~/.local/share/Anki2/addons21/`

3. **Backup old version (if exists):**
   ```
   Rename "Nottorney_Addon" to "Nottorney_Addon_OLD"
   ```

4. **Copy new addon:**
   - Copy the entire `Nottorney_Addon` folder from this package
   - Paste it into the `addons21` directory

5. **Restart Anki**

6. **Verify installation:**
   - Open Anki
   - Go to: Tools → ⚖️ Nottorney → Open Nottorney
   - You should see the new tabbed interface! ✅

---

## 🧪 Testing the New Features

After installation:

1. **Open Anki**
2. **Go to:** Tools → ⚖️ Nottorney → Open Nottorney
3. **New tabbed interface should appear** ✅
4. **Test login** (if you have an account)
5. **Browse the new tabs:**
   - My Decks: Shows your downloaded decks
   - Browse: Search and download decks
   - Updates: Check for available updates
6. **Test update checking:**
   - Click "🔍 Check Now" in Updates tab
   - Or use: Tools → ⚖️ Nottorney → Check for Updates

---

## 📋 File Structure (Updated)

```
Nottorney_Addon/
├── __init__.py              # Main entry point (ENHANCED v1.1.0)
├── api_client.py            # API client (ENHANCED - 14 new endpoints)
├── config.py                # Configuration (ENHANCED - update tracking)
├── deck_importer.py         # Deck import functionality
├── sync.py                  # Progress sync
├── update_checker.py        # NEW: Update checking service
├── config.json              # Default configuration
├── manifest.json            # Addon metadata (v1.1.0)
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git attributes
└── ui/
    ├── __init__.py         # UI package init
    ├── single_dialog.py    # Minimal dialog (legacy support)
    └── tabbed_dialog.py    # NEW: Modern tabbed interface
```

---

## 🔧 Technical Details

### v1.1.0 New Features

| Component | New Functionality | File |
|-----------|------------------|------|
| Update Checking | Automatic background checks | `update_checker.py` |
| API Client | 14 new endpoints (updates, notifications, sync) | `api_client.py` |
| Configuration | Update tracking, sync state, protected fields | `config.py` |
| UI | Modern tabbed interface | `ui/tabbed_dialog.py` |
| Entry Point | Auto-update check on startup | `__init__.py` |

### New API Endpoints Integrated

1. ✅ `check_updates()` - Check for deck updates
2. ✅ `get_changelog()` - Get version history
3. ✅ `check_notifications()` - Check user notifications
4. ✅ `batch_download_decks()` - Download multiple decks
5. 🔜 `push_changes()` - Push local edits (Phase 3)
6. 🔜 `pull_changes()` - Pull publisher updates (Phase 3)
7. 🔜 `submit_suggestion()` - Submit card improvements (Phase 3)
8. 🔜 `get_protected_fields()` - Manage protected fields (Phase 3)
9. 🔜 `get_card_history()` - View card history (Phase 3)
10. 🔜 `rollback_card()` - Rollback to previous version (Phase 3)
11. 🔜 `sync_tags()` - Sync tags bidirectionally (Phase 3)
12. 🔜 `sync_suspend_state()` - Sync suspend state (Phase 3)
13. 🔜 `sync_media()` - Sync media files (Phase 3)
14. 🔜 `sync_note_types()` - Sync note types (Phase 3)

✅ = Implemented in v1.1.0  
🔜 = Backend-ready, UI coming in Phase 3

### Configuration Options (New)

The addon now stores additional configuration:

```json
{
  "ui_mode": "tabbed",
  "auto_check_updates": true,
  "update_check_interval_hours": 24,
  "last_update_check": "2024-12-15T10:00:00",
  "available_updates": {},
  "sync_state": {},
  "protected_fields": {}
}
```

You can edit these in: Tools → Add-ons → Nottorney → Config

---

## 🎯 Quick Start Guide

### First Time Setup:

1. **Install the addon** (see Installation above)
2. **Restart Anki**
3. **Open Nottorney:** Tools → ⚖️ Nottorney → Open Nottorney
4. **Login** with your Nottorney account
5. **The addon will automatically check for updates** on first login

### Daily Usage:

1. **Open Anki** - Addon auto-checks for updates (once every 24 hours)
2. **Check Updates tab** - See if any decks have new versions
3. **Click "Update All"** - Download all available updates at once
4. **Browse tab** - Discover new decks to purchase/download
5. **My Decks tab** - View your collection with status indicators

### Update Checking:

**Automatic (Default):**
- Checks every 24 hours when you open Anki
- Shows notification badge if updates available
- No user action required

**Manual:**
- Open Nottorney → Go to Updates tab
- Click "🔍 Check Now"
- Or: Tools → ⚖️ Nottorney → Check for Updates

### Understanding Status Indicators:

- 🟢 **Green** = Up to date
- 🟡 **Yellow** = Update available
- ✓ **Checkmark** = Already downloaded
- 🔔 **Badge** = Unread updates/notifications

---

## 🐛 Troubleshooting

### Issue: "Update check failed"
**Solution:** 
1. Check your internet connection
2. Verify you're logged in
3. Try: Tools → ⚖️ Nottorney → Check for Updates

### Issue: "Tabs not showing"
**Solution:** 
1. Check config: Tools → Add-ons → Nottorney → Config
2. Ensure `"ui_mode": "tabbed"`
3. Restart Anki

### Issue: "Updates tab shows 0 updates but I know there are some"
**Solution:**
1. Click "🔍 Check Now" in Updates tab
2. Or manually check: Tools → ⚖️ Nottorney → Check for Updates

### Issue: "Old single-dialog interface appears"
**Solution:**
1. Go to: Tools → Add-ons → Nottorney → Config
2. Change `"ui_mode"` from `"minimal"` to `"tabbed"`
3. Restart Anki

### Issue: "Auto-update check not working"
**Solution:**
1. Open config: Tools → Add-ons → Nottorney → Config
2. Verify `"auto_check_updates": true`
3. Check `"update_check_interval_hours"` (default: 24)
4. Restart Anki

### Previous Issues (v1.0.2):
All previous issues from v1.0.2 are still fixed. See original README for details.

---

## ⚙️ Configuration

### Access Configuration:
1. Go to: Tools → Add-ons
2. Select "Nottorney"
3. Click "Config"

### Key Settings:

```json
{
  "ui_mode": "tabbed",              // "tabbed" or "minimal"
  "auto_check_updates": true,       // Enable auto-update checking
  "update_check_interval_hours": 24, // How often to check (hours)
  "auto_sync_enabled": true,        // Enable auto progress sync
  "api_url": "https://...",         // API endpoint (don't change)
  "downloaded_decks": {},           // Downloaded decks (auto-managed)
  "access_token": null,             // Login token (auto-managed)
  "available_updates": {}           // Available updates (auto-managed)
}
```

### Recommended Settings:

**For Active Users:**
```json
{
  "auto_check_updates": true,
  "update_check_interval_hours": 12,
  "auto_sync_enabled": true
}
```

**For Privacy-Conscious Users:**
```json
{
  "auto_check_updates": false,
  "auto_sync_enabled": false
}
```

---

## 🆕 Version History

### v1.1.0 (December 15, 2024) - CURRENT
- ✨ NEW: Automatic update checking
- ✨ NEW: Modern tabbed interface (My Decks, Browse, Updates)
- ✨ NEW: Visual status indicators (🟢🟡✓)
- ✨ NEW: Update notification badges
- ✨ NEW: Batch download support (up to 10 decks)
- ✨ NEW: 14 additional API endpoints integrated
- ✨ NEW: `update_checker.py` module
- ✨ NEW: `ui/tabbed_dialog.py` interface
- 🔧 Enhanced `api_client.py` with all AnkiHub-parity endpoints
- 🔧 Enhanced `config.py` with update tracking
- 🔧 Enhanced `__init__.py` with auto-check on startup
- 📝 Updated manifest to v1.1.0

### v1.0.2 (December 15, 2024)
- ✅ Fixed browse_decks missing `action` parameter
- ✅ Fixed response format handling
- ✅ Fixed deck field names (`title` instead of `name`)
- ✅ Enhanced .gitignore

### v1.0.1 (December 15, 2024)
- Fixed all PyQt6 compatibility issues
- Improved deck import handling
- Better error messages
- Enhanced config management

### v1.0.0 (Original)
- Initial release
- Basic deck download
- Progress sync

---

## 🔮 Roadmap

### Phase 2: Notifications (Week 5) - IN PROGRESS
- [ ] Notification checking
- [ ] Notification badge in toolbar
- [ ] Notification list dialog
- [ ] Mark as read functionality

### Phase 3: AnkiHub-Parity (Week 6-8) - PLANNED
- [ ] Push/pull card changes
- [ ] Conflict resolution UI
- [ ] Protected fields UI
- [ ] Card suggestion system
- [ ] Card history viewer
- [ ] Rollback functionality

### Phase 4: Advanced Sync (Week 9-10) - PLANNED
- [ ] Tag synchronization
- [ ] Suspend state sync
- [ ] Media file sync
- [ ] Note type template sync

---

## ⚠️ Known Limitations

1. **Anki 23.x and earlier:** Not compatible (requires PyQt6)
2. **Batch download:** Limited to 10 decks per request (API limit)
3. **Update checking:** Requires internet connection
4. **Network errors:** Limited automatic retry logic
5. **Large decks:** May take time depending on connection speed

---

## 🔗 Support & Resources

- **Homepage:** https://nottorney.lovable.app
- **API Documentation:** See `nottorney_api_docs_Version2.md`
- **Report Issues:** Contact Nottorney support
- **Anki Version Check:** Help → About Anki
- **Addon Version:** v1.1.0

---

## 📄 License

Copyright © 2024 Nottorney Team  
All rights reserved.

---

## 🎓 For Law Students in the Philippines

This addon is specifically designed for law students using Nottorney's Philippine law decks. The update system ensures you always have the latest jurisprudence, statutory amendments, and bar exam coverage.

### Recommended Workflow:

1. **Weekly Check:** Open Nottorney every week to check for updates
2. **Before Bar Review:** Always update all decks before intensive review
3. **After Major Supreme Court Rulings:** Check for deck updates
4. **Progress Sync:** Let the addon sync your study progress automatically

### Study Tips:

- Enable auto-update checking to stay current with legal developments
- Use the "My Decks" tab to track your study progress
- Download updates immediately to ensure accuracy for exams

---

**Stay Updated. Study Smart. Pass the Bar! 📚⚖️**