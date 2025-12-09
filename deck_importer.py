"""
Deck importer for the Nottorney addon
Handles importing .apkg files into Anki with modern compression support
"""

import tempfile
import os
from pathlib import Path
from aqt import mw
from aqt.operations import QueryOp

# Use the modern importer that handles zstd compression
from anki.importing.anki2 import AnkiPackageImporter


def import_deck(deck_content: bytes, deck_title: str) -> int:
    """
    Import a deck into Anki from .apkg file content
    
    Args:
        deck_content: The .apkg file content as bytes
        deck_title: Title of the deck (for reference)
    
    Returns:
        The Anki deck ID of the imported deck
    
    Raises:
        Exception: If import fails
    """
    if not deck_content:
        raise ValueError("Deck content is empty")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as f:
        f.write(deck_content)
        temp_path = f.name
    
    print(f"Created temp file: {temp_path} ({len(deck_content)} bytes)")
    
    try:
        # Use the modern importer that handles zstd compression
        print("Starting import with AnkiPackageImporter...")
        importer = AnkiPackageImporter(mw.col, temp_path)
        importer.run()
        
        # Get the deck ID from the importer
        deck_id = importer.dst_deck_id
        print(f"Import successful! Deck ID: {deck_id}")
        
        # Refresh the main window to show the new deck
        mw.reset()
        
        return deck_id
    
    except Exception as e:
        print(f"Import failed: {e}")
        raise Exception(f"Failed to import deck: {str(e)}")
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
            print(f"Cleaned up temp file")
        except Exception as e:
            print(f"Warning: Failed to delete temp file: {e}")


def import_deck_with_progress(deck_content: bytes, deck_name: str, 
                              on_success=None, on_failure=None):
    """
    Import a deck with progress tracking (runs in background)
    
    Args:
        deck_content: The .apkg file content as bytes
        deck_name: Name of the deck
        on_success: Callback function when import succeeds (receives deck_id)
        on_failure: Callback function when import fails (receives error message)
    """
    def import_in_background():
        return import_deck(deck_content, deck_name)
    
    def on_done(deck_id):
        if on_success:
            on_success(deck_id)
    
    def on_error(error):
        error_msg = str(error)
        if on_failure:
            on_failure(error_msg)
    
    # Use Anki's QueryOp for background operations
    op = QueryOp(
        parent=mw,
        op=lambda col: import_in_background(),
        success=on_done
    )
    op.failure(on_error)
    op.run_in_background()


def get_deck_stats(deck_id: int) -> dict:
    """
    Get statistics for a deck
    
    Args:
        deck_id: The Anki deck ID
    
    Returns:
        Dictionary with deck statistics
    """
    try:
        deck = mw.col.decks.get(deck_id)
        
        if not deck:
            print(f"Deck ID {deck_id} not found")
            return {}
        
        # Get card counts
        card_ids = mw.col.decks.cids(deck_id, children=True)
        total_cards = len(card_ids)
        
        # Count cards by type
        new_cards = 0
        learning_cards = 0
        review_cards = 0
        suspended_cards = 0
        
        for card_id in card_ids:
            try:
                card = mw.col.get_card(card_id)
                
                # Check if suspended
                if card.queue == -1:
                    suspended_cards += 1
                    continue
                
                # Count by type
                if card.type == 0:  # New
                    new_cards += 1
                elif card.type == 1:  # Learning/relearning
                    learning_cards += 1
                elif card.type == 2:  # Review
                    review_cards += 1
            except Exception as e:
                print(f"Error getting card {card_id}: {e}")
                continue
        
        return {
            'name': deck['name'],
            'deck_id': deck_id,
            'total_cards': total_cards,
            'new_cards': new_cards,
            'learning_cards': learning_cards,
            'review_cards': review_cards,
            'suspended_cards': suspended_cards
        }
    
    except Exception as e:
        print(f"Error getting deck stats for {deck_id}: {e}")
        return {}


def get_all_deck_stats() -> list:
    """
    Get statistics for all decks
    
    Returns:
        List of deck statistics dictionaries
    """
    try:
        all_decks = mw.col.decks.all()
        stats = []
        
        for deck in all_decks:
            deck_id = deck['id']
            deck_stats = get_deck_stats(deck_id)
            if deck_stats:
                stats.append(deck_stats)
        
        return stats
    
    except Exception as e:
        print(f"Error getting all deck stats: {e}")
        return []