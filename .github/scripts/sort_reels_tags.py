"""
Sort Instagram Reels by Tag

This script:
- Reads links/reels.md
- Lists all unique hashtags
- Lets you choose a tag by number
- Moves all entries with that tag to links/{tag}.md
- Removes those entries from reels.md

Usage:
    python3.11 .github/scripts/sort_reels_tags.py
"""

import os
import re
from collections import Counter

# Paths
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
REELS_FILE = os.path.join(WORKSPACE_ROOT, 'links', 'reels.md')
LINKS_DIR = os.path.join(WORKSPACE_ROOT, 'links')

# Tags to ignore (system/metadata tags)
IGNORE_TAGS = ['#untag', '#enrich', '#en-US', '#pt-BR', '#es-ES', '#ja-JP', '#ko-KR',
               '#zh-CN', '#zh-TW', '#ar-SA', '#ru-RU', '#fr-FR', '#de-DE', '#it-IT']

def extract_hashtags(line):
    """Extract all hashtags from a line."""
    # Find all hashtags (word characters, hyphens, underscores after #)
    return re.findall(r'#[\w\-]+', line)

def is_date_tag(tag):
    """Check if tag looks like a date (#2025-12-30)."""
    return bool(re.match(r'#\d{4}-\d{2}-\d{2}', tag))

def read_reels():
    """Read all lines from reels.md."""
    if not os.path.exists(REELS_FILE):
        print(f"✗ File not found: {REELS_FILE}")
        return []

    with open(REELS_FILE, 'r') as f:
        return [line.rstrip() for line in f if line.strip()]

def get_tag_counts(lines):
    """Count all hashtags across all lines (excluding system tags and dates)."""
    tag_counter = Counter()

    for line in lines:
        tags = extract_hashtags(line)
        for tag in tags:
            if tag not in IGNORE_TAGS and not is_date_tag(tag):
                tag_counter[tag] += 1

    return tag_counter

def filter_lines_by_tag(lines, selected_tag):
    """Separate lines into those with the tag and those without."""
    with_tag = []
    without_tag = []

    for line in lines:
        tags = extract_hashtags(line)
        if selected_tag in tags:
            with_tag.append(line)
        else:
            without_tag.append(line)

    return with_tag, without_tag

def save_to_file(filepath, lines):
    """Save lines to a file."""
    with open(filepath, 'w') as f:
        for line in lines:
            f.write(line + '\n')

def main():
    print("📱 Instagram Reels Tag Sorter\n")

    # Read reels
    lines = read_reels()
    if not lines:
        print("No entries found in reels.md")
        return

    print(f"Found {len(lines)} entries in reels.md\n")

    # Get tag counts
    tag_counts = get_tag_counts(lines)

    if not tag_counts:
        print("No sortable tags found")
        return

    # Display tags
    print("Available tags:\n")
    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

    # Show tags in columns for compact display
    for idx, (tag, count) in enumerate(sorted_tags, 1):
        print(f"  {idx:3d}. {tag}")

    print("\n    0. Cancel")

    # Get user choice
    try:
        choice = int(input("\nSelect tag number to sort: "))

        if choice == 0:
            print("Cancelled")
            return

        if choice < 1 or choice > len(sorted_tags):
            print("Invalid selection")
            return

        selected_tag, count = sorted_tags[choice - 1]

    except (ValueError, KeyboardInterrupt):
        print("\nCancelled")
        return

    print(f"\nProcessing tag: {selected_tag} ({count} entries)")

    # Filter lines
    with_tag, without_tag = filter_lines_by_tag(lines, selected_tag)

    # Determine output filename (remove # from tag)
    tag_name = selected_tag.replace('#', '')
    output_file = os.path.join(LINKS_DIR, f"{tag_name}.md")

    # Auto-append if file exists
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing = [line.rstrip() for line in f if line.strip()]
        with_tag = existing + with_tag
        print(f"  Appending {count} entries to existing {tag_name}.md")

    # Save files
    save_to_file(output_file, with_tag)
    save_to_file(REELS_FILE, without_tag)

    print(f"\n✓ Complete!")
    print(f"  Moved {count} entries to: links/{tag_name}.md")
    print(f"  Remaining in reels.md: {len(without_tag)}")

if __name__ == "__main__":
    main()
