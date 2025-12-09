"""
Deck importer for the Ottorney addon
Handles importing .apkg files into Anki
"""

import tempfile
import os
from pathlib import Path
from aqt import mw
from aqt.operations import QueryOp
from anki.importing import AnkiPackageImporter


def import_deck(deck_content: bytes, deck_name: str) -> int:
    """
    Import a deck into Anki from .apkg file content
    
    Args:
        deck_content: The .apkg file content as bytes
        deck_name: Name of the deck
    
    Returns:
        The Anki deck ID of the imported deck
    """
    # Create a temporary file to store the .apkg
    with tempfile.NamedTemporaryFile(suffix='.apkg', delete=False) as temp_file:
        temp_file.write(deck_content)
        temp_file_path = temp_file.name
    
    try:
        # Import the deck using Anki's importer
        importer = AnkiPackageImporter(mw.col, temp_file_path)
        
        # Run the import
        importer.run()
        
        # Get the deck ID
        # The importer usually creates a deck with the name from the package
        # or uses an existing deck with that name
        deck_id = mw.col.decks.id(deck_name)
        
        # Refresh the main window to show the new deck
        mw.reset()
        
        return deck_id
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass


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
    deck = mw.col.decks.get(deck_id)
    
    if not deck:
        return {}
    
    # Get card counts
    card_ids = mw.col.decks.cids(deck_id, children=True)
    total_cards = len(card_ids)
    
    # Count new, learning, and review cards
    new_cards = 0
    learning_cards = 0
    review_cards = 0
    
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        if card.type == 0:  # New
            new_cards += 1
        elif card.type == 1:  # Learning
            learning_cards += 1
        elif card.type == 2:  # Review
            review_cards += 1
    
    return {
        'name': deck['name'],
        'total_cards': total_cards,
        'new_cards': new_cards,
        'learning_cards': learning_cards,
        'review_cards': review_cards
    }


def get_all_deck_stats() -> list:
    """
    Get statistics for all decks
    
    Returns:
        List of deck statistics
    """
    all_decks = mw.col.decks.all()
    stats = []
    
    for deck in all_decks:
        deck_id = deck['id']
        deck_stats = get_deck_stats(deck_id)
        if deck_stats:
            stats.append(deck_stats)
    
    return stats
