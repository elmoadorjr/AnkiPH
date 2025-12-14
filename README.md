# Nottorney Anki Addon - Fixed for PyQt6

**Version:** 1.0.1  
**Fixed:** December 14, 2024  
**Compatible with:** Anki 24.x - 25.x (PyQt6)

---

## ✅ What Was Fixed

This version fixes **PyQt6 compatibility issues** that were causing the addon to crash on modern Anki versions.

### Main Fixes:

1. **QLineEdit.Password → QLineEdit.EchoMode.Password**
   - Fixed password field visibility in login dialog
   - Location: `ui/single_dialog.py` line 51

2. **Qt.UserRole → Qt.ItemDataRole.UserRole**
   - Fixed deck list item data storage/retrieval
   - Locations: `ui/single_dialog.py` lines 129, 146

3. **DeckNameId handling**
   - Properly extracts integer deck IDs from Anki's DeckNameId objects
   - Location: `deck_importer.py`

4. **API improvements**
   - Fixed sync_progress to accept progress_data parameter
   - Better error handling throughout

---

## 📦 Installation

### Method 1: Replace Files (Recommended)

1. **Close Anki completely**

2. **Navigate to your Anki addons folder:**
   - **Windows:** `C:\Users\[YourUsername]\AppData\Roaming\Anki2\addons21\`
   - **Mac:** `~/Library/Application Support/Anki2/addons21/`
   - **Linux:** `~/.local/share/Anki2/addons21/`

3. **Backup your current addon:**
   ```
   Rename "Nottorney_Addon" to "Nottorney_Addon_OLD"
   ```

4. **Copy the fixed addon:**
   - Copy the entire `Nottorney_Addon` folder from this package
   - Paste it into the `addons21` directory

5. **Restart Anki**

### Method 2: Manual File Replacement

If you want to keep your config/settings:

1. Close Anki
2. Only replace these files in your existing addon folder:
   - `__init__.py`
   - `api_client.py`
   - `config.py`
   - `deck_importer.py`
   - `sync.py`
   - `ui/single_dialog.py`
3. Restart Anki

---

## 🧪 Testing the Fix

After installation:

1. **Open Anki**
2. **Go to:** Tools → Nottorney → Open
3. **The dialog should now open without errors**
4. **Test login** (if you have an account)
5. **Test deck browsing** (after login)

If you see the login dialog without any error messages, the fix is working! ✅

---

## 📋 File Structure

```
Nottorney_Addon/
├── __init__.py              # Main addon entry point (FIXED)
├── api_client.py            # API communication (IMPROVED)
├── config.py                # Configuration management (IMPROVED)
├── deck_importer.py         # Deck import functionality (FIXED)
├── sync.py                  # Progress sync (FIXED)
├── config.json              # Default configuration
├── manifest.json            # Addon metadata
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git attributes
└── ui/
    ├── __init__.py         # UI package init
    └── single_dialog.py    # Main dialog (FIXED - PyQt6)
```

---

## 🔧 Technical Details

### PyQt5 vs PyQt6 Enum Changes

| Feature | PyQt5 (Old) | PyQt6 (New) |
|---------|-------------|-------------|
| Password field | `QLineEdit.Password` | `QLineEdit.EchoMode.Password` |
| User data role | `Qt.UserRole` | `Qt.ItemDataRole.UserRole` |
| Alignment | `Qt.AlignCenter` | `Qt.AlignmentFlag.AlignCenter` |
| Message box icons | `QMessageBox.Warning` | `QMessageBox.Icon.Warning` |

### Changes Summary

**ui/single_dialog.py:**
- Line 51: Added `.EchoMode` to password field
- Line 129: Added `.ItemDataRole` to setData call
- Line 146: Added `.ItemDataRole` to data retrieval

**deck_importer.py:**
- Properly handles DeckNameId objects from `mw.col.decks.all_names_and_ids()`
- Extracts integer ID with `deck_info.id`
- Returns integer deck IDs consistently

**api_client.py:**
- Fixed `sync_progress()` to accept `progress_data` parameter
- Improved error messages

---

## 🐛 Troubleshooting

### Issue: "AttributeError: type object 'QLineEdit' has no attribute 'Password'"
**Solution:** You're using the old version. Replace with this fixed version.

### Issue: "Module not found" errors
**Solution:** 
1. Make sure folder is named exactly `Nottorney_Addon`
2. Check that all files are present
3. Restart Anki completely

### Issue: Dialog won't open
**Solution:**
1. Check Anki's error log: Tools → Add-ons → View Files → addons21 → errors.log
2. Disable other addons temporarily to check for conflicts
3. Make sure you're using Anki 24.x or later

### Issue: "Config is None" warnings
**Solution:** This is normal on first run. The addon will create default config automatically.

---

## 📝 Configuration

The addon stores configuration in Anki's addon manager. You can manually edit if needed:

1. Go to: Tools → Add-ons
2. Select "Nottorney"
3. Click "Config"

Key settings:
- `api_url`: API endpoint (default: Supabase function)
- `auto_sync_enabled`: Enable automatic progress sync
- `downloaded_decks`: Tracks downloaded decks

---

## 🆕 What's New in v1.0.1

- ✅ Full PyQt6 compatibility
- ✅ Fixed password field visibility
- ✅ Fixed deck list item data handling
- ✅ Improved DeckNameId handling
- ✅ Better error messages
- ✅ Improved API sync functionality
- ✅ Better deck cleanup on removal

---

## ⚠️ Known Limitations

1. **Anki 23.x and earlier:** Not compatible (uses PyQt5)
2. **Multiple decks:** API might have rate limits on batch downloads
3. **Network errors:** Limited retry logic (fails fast)

---

## 🔗 Support

- **Homepage:** https://nottorney.lovable.app
- **Issues:** Report via GitHub or contact support
- **Anki Version:** Check with Help → About Anki

---

## 📄 License

Copyright © 2024 Nottorney Team  
All rights reserved.

---

## 🎯 Quick Start Guide

1. **Install the addon** (see Installation above)
2. **Restart Anki**
3. **Open Nottorney:** Tools → Nottorney → Open
4. **Login** with your Nottorney account
5. **Browse decks** in the catalog
6. **Download** decks you've purchased
7. **Study** normally in Anki
8. **Progress syncs** automatically

---

## 🔍 Version History

### v1.0.1 (December 14, 2024)
- Fixed PyQt6 compatibility issues
- Improved deck import handling
- Better error messages
- Enhanced config management

### v1.0.0 (Original)
- Initial release
- Basic deck download functionality
- Progress sync
- PyQt5 compatible only

---

**Enjoy studying with Nottorney! 📚⚖️**