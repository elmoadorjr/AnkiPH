"""
Progress syncing for the Nottorney addon - FIXED VERSION
Syncs study progress to the server with improved error handling
"""

from aqt import mw
from datetime import datetime, timedelta
from .api_client import api
from .config import config
from .deck_importer import get_deck_stats


def deck_exists(anki_deck_id):
    """Check if a deck exists in Anki's collection"""
    try:
        if not mw.col:
            print("Collection not available")
            return False
        deck = mw.col.decks.get(anki_deck_id)
        return deck is not None
    except Exception as e:
        print(f"Error checking deck existence: {e}")
        return False


def get_progress_data() -> list:
    """
    Get progress data for all downloaded Nottorney decks
    
    Returns:
        List of progress data dictionaries
    """
    downloaded_decks = config.get_downloaded_decks()
    progress_data = []
    decks_to_remove = []
    
    for deck_id, deck_info in downloaded_decks.items():
        anki_deck_id = deck_info.get('anki_deck_id')
        
        if not anki_deck_id:
            print(f"Deck {deck_id} has no Anki ID, skipping...")
            continue
        
        # Check if deck still exists in Anki
        if not deck_exists(anki_deck_id):
            print(f"Deck {deck_id} (Anki ID: {anki_deck_id}) no longer exists, marking for removal...")
            decks_to_remove.append(deck_id)
            continue
        
        try:
            # Get deck statistics
            stats = get_deck_stats(anki_deck_id)
            
            if not stats:
                print(f"No stats for deck {deck_id}, using defaults...")
                stats = {
                    'total_cards': 0,
                    'new_cards': 0,
                    'learning_cards': 0,
                    'review_cards': 0
                }
            
            # Get review statistics from the last 30 days
            review_stats = get_review_stats_for_deck(anki_deck_id, days=30)
            
            # Calculate retention rate
            retention_rate = calculate_retention_rate(anki_deck_id)
            
            # Calculate current streak
            current_streak = calculate_current_streak(anki_deck_id)
            
            # Build progress data
            progress = {
                'deck_id': deck_id,
                'total_cards': stats.get('total_cards', 0),
                'total_cards_studied': review_stats.get('total_reviews', 0),
                'new_cards_studied': review_stats.get('new_cards', 0),
                'cards_mastered': stats.get('review_cards', 0),
                'average_ease': review_stats.get('average_ease', 0),
                'study_time_minutes': review_stats.get('study_time_minutes', 0),
                'last_study_date': review_stats.get('last_study_date'),
                'retention_rate': retention_rate,
                'current_streak_days': current_streak,
                'synced_at': datetime.now().isoformat()
            }
            
            progress_data.append(progress)
            print(f"Prepared progress data for deck {deck_id}")
            
        except Exception as e:
            print(f"Error processing deck {deck_id}: {e}")
            continue
    
    # Clean up decks that no longer exist
    for deck_id in decks_to_remove:
        config.remove_downloaded_deck(deck_id)
        print(f"Removed non-existent deck {deck_id} from tracking")
    
    return progress_data


def calculate_retention_rate(deck_id: int) -> float:
    """
    Calculate retention rate for a deck based on review performance
    
    Retention rate = (Correct reviews / Total reviews) * 100
    Only considers reviews from the last 30 days
    """
    try:
        if not mw.col or not deck_exists(deck_id):
            return 0.0
        
        # Calculate the timestamp for 30 days ago
        cutoff_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        
        # Get card IDs for the deck
        card_ids = mw.col.decks.cids(deck_id, children=True)
        
        if not card_ids:
            return 0.0
        
        # FIXED: Validate card_ids before building query
        valid_card_ids = [int(cid) for cid in card_ids if cid]
        if not valid_card_ids:
            return 0.0
        
        card_ids_str = ",".join(str(cid) for cid in valid_card_ids)
        
        # FIXED: Added error handling for SQL query
        query = f"""
            SELECT 
                COUNT(*) as total_reviews,
                SUM(CASE WHEN ease >= 2 THEN 1 ELSE 0 END) as correct_reviews
            FROM revlog
            WHERE cid IN ({card_ids_str})
            AND id >= {cutoff_time}
        """
        
        result = mw.col.db.first(query)
        
        if not result or result[0] == 0:
            return 0.0
        
        total_reviews = result[0]
        correct_reviews = result[1] or 0
        
        retention_rate = (correct_reviews / total_reviews) * 100
        
        return round(retention_rate, 2)
    
    except Exception as e:
        print(f"Error calculating retention rate for deck {deck_id}: {e}")
        return 0.0


def calculate_current_streak(deck_id: int) -> int:
    """
    Calculate the current study streak for a deck
    
    A streak is maintained if the user studied at least once per day.
    The streak breaks if there's a day with no reviews.
    """
    try:
        if not mw.col or not deck_exists(deck_id):
            return 0
        
        # Get card IDs for the deck
        card_ids = mw.col.decks.cids(deck_id, children=True)
        
        if not card_ids:
            return 0
        
        # FIXED: Validate card_ids
        valid_card_ids = [int(cid) for cid in card_ids if cid]
        if not valid_card_ids:
            return 0
        
        card_ids_str = ",".join(str(cid) for cid in valid_card_ids)
        
        # FIXED: Added error handling and better date parsing
        query = f"""
            SELECT DISTINCT DATE(id / 1000, 'unixepoch', 'localtime') as review_date
            FROM revlog
            WHERE cid IN ({card_ids_str})
            ORDER BY review_date DESC
        """
        
        review_dates = mw.col.db.list(query)
        
        if not review_dates:
            return 0
        
        # FIXED: Better date parsing with error handling
        parsed_dates = []
        for date_str in review_dates:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                parsed_dates.append(parsed_date)
            except ValueError as e:
                print(f"Error parsing date '{date_str}': {e}")
                continue
        
        if not parsed_dates:
            return 0
        
        # Check if user studied today or yesterday to count as active streak
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        if parsed_dates[0] != today and parsed_dates[0] != yesterday:
            # Streak is broken if last review was before yesterday
            return 0
        
        # Count consecutive days
        streak_days = 0
        expected_date = today
        
        for review_date in parsed_dates:
            if review_date == expected_date or review_date == expected_date - timedelta(days=1):
                streak_days += 1
                expected_date = review_date - timedelta(days=1)
            else:
                # Gap found, streak ends
                break
        
        return streak_days
    
    except Exception as e:
        print(f"Error calculating streak for deck {deck_id}: {e}")
        return 0


def get_review_stats_for_deck(deck_id: int, days: int = 30) -> dict:
    """
    Get review statistics for a deck from the review history
    """
    try:
        if not mw.col or not deck_exists(deck_id):
            return {}
        
        # Calculate the timestamp for X days ago
        cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Get card IDs for the deck
        card_ids = mw.col.decks.cids(deck_id, children=True)
        
        if not card_ids:
            return {}
        
        # FIXED: Validate card_ids
        valid_card_ids = [int(cid) for cid in card_ids if cid]
        if not valid_card_ids:
            return {}
        
        card_ids_str = ",".join(str(cid) for cid in valid_card_ids)
        
        # FIXED: Added error handling for SQL query
        query = f"""
            SELECT 
                COUNT(*) as total_reviews,
                SUM(CASE WHEN type = 0 THEN 1 ELSE 0 END) as new_cards,
                AVG(ease) as average_ease,
                SUM(time) / 60000 as study_time_minutes,
                MAX(id) as last_review_id
            FROM revlog
            WHERE cid IN ({card_ids_str})
            AND id >= {cutoff_time}
        """
        
        result = mw.col.db.first(query)
        
        if not result:
            return {}
        
        # Get last study date from the last review ID
        last_study_date = None
        if result[4]:  # last_review_id
            try:
                last_study_date = datetime.fromtimestamp(result[4] / 1000).isoformat()
            except (ValueError, OSError) as e:
                print(f"Error converting timestamp {result[4]}: {e}")
        
        return {
            'total_reviews': result[0] or 0,
            'new_cards': result[1] or 0,
            'average_ease': round(result[2] or 0, 2),
            'study_time_minutes': round(result[3] or 0, 2),
            'last_study_date': last_study_date
        }
    except Exception as e:
        print(f"Error getting review stats for deck {deck_id}: {e}")
        return {}


def clean_deleted_decks():
    """
    Remove tracking for decks that no longer exist in Anki
    Returns the number of decks cleaned up
    """
    downloaded_decks = config.get_downloaded_decks()
    decks_to_remove = []
    
    for deck_id, deck_info in downloaded_decks.items():
        anki_deck_id = deck_info.get('anki_deck_id')
        
        if not anki_deck_id:
            decks_to_remove.append(deck_id)
            continue
        
        if not deck_exists(anki_deck_id):
            decks_to_remove.append(deck_id)
            print(f"Deck {deck_id} (Anki ID: {anki_deck_id}) marked for cleanup")
    
    # Remove the deleted decks from tracking
    for deck_id in decks_to_remove:
        config.remove_downloaded_deck(deck_id)
        print(f"Removed deck {deck_id} from tracking")
    
    return len(decks_to_remove)


def sync_progress():
    """
    Sync progress for all downloaded decks to the server
    """
    # FIXED: Check if collection is available
    if not mw.col:
        raise Exception("Anki collection not available. Please try again.")
    
    if not config.is_logged_in():
        raise Exception("Not logged in")
    
    try:
        # First, clean up any deleted decks
        cleaned = clean_deleted_decks()
        if cleaned > 0:
            print(f"Cleaned up {cleaned} deleted deck(s) from tracking")
        
        # Get progress data
        progress_data = get_progress_data()
        
        if not progress_data:
            # No decks to sync
            print("No decks to sync")
            return None
        
        # Send to server
        print(f"Syncing progress for {len(progress_data)} deck(s)")
        result = api.sync_progress(progress_data)
        
        return result
    
    except Exception as e:
        print(f"Sync progress error: {e}")
        raise


def should_auto_sync() -> bool:
    """
    Check if we should automatically sync progress
    """
    return True


def auto_sync_if_needed():
    """
    Automatically sync progress if needed
    """
    if not config.is_logged_in():
        return
    
    if not mw.col:
        return
    
    if not should_auto_sync():
        return
    
    try:
        sync_progress()
    except Exception as e:
        # Silently fail for auto-sync
        print(f"Auto-sync failed: {e}")