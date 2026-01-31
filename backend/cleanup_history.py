#!/usr/bin/env python3
"""
Cleanup script to merge duplicate YouTube transcript + translation entries.
Run this once to fix existing history.json files.
"""

import json
import sys
from pathlib import Path

def cleanup_history():
    # Path to history.json
    history_file = Path("data/history.json")
    
    if not history_file.exists():
        print("No history.json found, nothing to cleanup")
        return
    
    # Load history
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    print(f"Found {len(history)} entries")
    
    # Group entries by video_id for YouTube entries
    youtube_entries = {}
    text_entries = []
    other_entries = []
    
    for entry in history:
        if entry.get("type") == "youtube" and entry.get("video_id"):
            video_id = entry["video_id"]
            if video_id not in youtube_entries:
                youtube_entries[video_id] = []
            youtube_entries[video_id].append(entry)
        elif entry.get("type") == "text":
            text_entries.append(entry)
        else:
            other_entries.append(entry)
    
    # Process each YouTube video group
    merged_entries = []
    text_entries_to_merge = []
    
    for video_id, entries in youtube_entries.items():
        if len(entries) == 1:
            # Single entry, keep as-is
            merged_entries.append(entries[0])
            continue
        
        # Multiple entries for same video - merge them
        print(f"Merging {len(entries)} entries for video {video_id}")
        
        # Find the entry with the most complete information
        best_entry = max(entries, key=lambda e: (
            len(e.get("original_text", "")),
            len(e.get("translated_text", "")),
            len(e.get("available_languages", []))
        ))
        
        # Merge information from all entries
        for entry in entries:
            if entry != best_entry:
                # Merge translated_text if the best entry doesn't have it
                if not best_entry.get("translated_text") and entry.get("translated_text"):
                    best_entry["translated_text"] = entry["translated_text"]
                    best_entry["target_lang"] = entry["target_lang"]
                    best_entry["provider"] = entry.get("provider", "youtube")
                    best_entry["updated_at"] = entry.get("created_at")
        
        merged_entries.append(best_entry)
    
    # Find text entries that match YouTube transcripts
    for text_entry in text_entries:
        matched = False
        text_clean = text_entry.get("original_text", "").replace("\n", " ").replace("\r", "").strip()
        
        for youtube_entry in merged_entries:
            if (youtube_entry.get("source_lang") == text_entry.get("source_lang") and
                not youtube_entry.get("translated_text")):
                
                original_clean = youtube_entry.get("original_text", "").replace("\n", " ").replace("\r", "").strip()
                
                # Check if texts match closely
                if (original_clean == text_clean or 
                    len(set(original_clean.split()) & set(text_clean.split())) > len(text_clean.split()) * 0.8):
                    
                    print(f"Merging text translation into YouTube entry: {youtube_entry.get('title', 'Untitled')}")
                    
                    # Update YouTube entry with translation
                    youtube_entry["translated_text"] = text_entry["translated_text"]
                    youtube_entry["target_lang"] = text_entry["target_lang"]
                    youtube_entry["provider"] = text_entry.get("provider", "libretranslate")
                    youtube_entry["updated_at"] = text_entry["created_at"]
                    
                    matched = True
                    break
        
        if not matched:
            text_entries_to_merge.append(text_entry)
    
    # Combine all entries
    final_history = merged_entries + text_entries_to_merge + other_entries
    
    # Sort by creation date (newest first)
    final_history.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    print(f"Reduced {len(history)} entries to {len(final_history)} entries")
    
    # Save backup
    backup_file = history_file.with_suffix('.json.backup')
    with open(backup_file, 'w') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"Backup saved to {backup_file}")
    
    # Save cleaned history
    with open(history_file, 'w') as f:
        json.dump(final_history, f, indent=2, ensure_ascii=False)
    
    print("History cleaned successfully!")

if __name__ == "__main__":
    cleanup_history()