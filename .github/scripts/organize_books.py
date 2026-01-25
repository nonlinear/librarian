#!/usr/bin/env python3
"""
Organize books from Downloads to personal library with interactive topic selection.

Workflow:
1. Rename all .epub/.pdf files in ~/Downloads (root only, not in subfolders)
2. Open ~/Downloads in Finder for manual editing
3. Pause for user to review/edit
4. For each book, list all topics/subtopics with numbers
5. User inputs matches (A3 B7 C14 D0)
6. Move books to corresponding folders (skip if 0)
"""

import json
import shutil
import subprocess
from pathlib import Path

# Configuration
DOWNLOADS_FOLDER = Path.home() / "Downloads"
LIBRARY_PATH = Path.home() / "Documents" / "personal library"
BOOKS_PATH = LIBRARY_PATH / "books"
METADATA_FILE = BOOKS_PATH / "metadata.json"

def load_topics():
    """Load topics from metadata.json"""
    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)
    return data['topics']

def get_books_in_downloads():
    """Get all .epub and .pdf files in Downloads root only"""
    books = []
    for file_path in DOWNLOADS_FOLDER.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.epub', '.pdf']:
            books.append(file_path)
    return sorted(books)

def rename_downloads():
    """Clean up filenames in Downloads (Anna's Archive format)"""
    print("\n📚 STEP 1: Renaming books in Downloads\n")

    books = get_books_in_downloads()
    if not books:
        print("⚠️  No .epub or .pdf files found in ~/Downloads root")
        return 0

    renamed_count = 0
    for file_path in books:
        original_name = file_path.name
        extension = file_path.suffix
        name_without_ext = file_path.stem

        # Remove " -- Anna's Archive" suffix if present
        name_without_ext = name_without_ext.replace(" -- Anna's Archive", "")

        # Extract title: everything before first " -- " or " - "
        if " -- " in name_without_ext:
            # Split on first " -- "
            title = name_without_ext.split(" -- ")[0].strip()
        elif " - " in name_without_ext:
            # Split on first " - "
            title = name_without_ext.split(" - ")[0].strip()
        else:
            # No separator, keep as is
            title = name_without_ext.strip()

        new_name = f"{title}{extension}"

        # Skip if already correct
        if original_name == new_name:
            print(f"   ✓ {original_name}")
            continue

        new_path = file_path.parent / new_name

        # Check if new name already exists
        if new_path.exists():
            print(f"   ⚠️  {original_name}")
            print(f"      → {new_name} (already exists, skipping)")
            continue

        # Rename
        try:
            file_path.rename(new_path)
            print(f"   ✅ {original_name}")
            print(f"      → {new_name}")
            renamed_count += 1
        except Exception as e:
            print(f"   ❌ Error renaming {original_name}: {e}")

    print(f"\n✅ Renamed {renamed_count} book(s), found {len(books)} total")

def get_all_book_folders():
    """Scan books directory for all folders (ignoring hidden folders)"""
    folders = []
    for item in BOOKS_PATH.rglob('*'):
        if item.is_dir() and not any(part.startswith('.') for part in item.parts):
            rel_path = item.relative_to(BOOKS_PATH)
            folders.append(str(rel_path))
    return sorted(folders)

def has_subfolders(folder_path):
    """Check if a folder has subfolders"""
    full_path = BOOKS_PATH / folder_path
    for item in full_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            return True
    return False

def display_topics_menu():
    """Display all topics and subtopics with numbers (only leaf folders)"""
    print("\n📂 Available Topics:\n")
    print("=" * 80)

    all_folders = get_all_book_folders()
    topic_map = {}  # Maps number to folder_path

    index = 1
    current_parent = None

    for folder in all_folders:
        parts = folder.split('/')

        # Check if this folder has subfolders
        is_leaf = not has_subfolders(folder)

        # Show parent folder as header if it changed
        if len(parts) > 1:
            parent = parts[0]
            if parent != current_parent:
                current_parent = parent
                print(f"\n{parent.upper()}/")
        elif current_parent is not None:
            # Single-level folder after multi-level ones
            current_parent = None
            print()

        # Calculate indentation
        indent = "  " * (len(parts) - 1)
        label = parts[-1]

        # Only number leaf folders (folders without subfolders)
        if is_leaf:
            topic_map[index] = folder
            print(f"{indent}{index:2d}. {label}")
            index += 1
        else:
            # Show as header only (not numbered)
            print(f"{indent}    {label.upper()}/")

    print("\n" + "=" * 80)
    print("0. Don't move (skip this book)")
    print("=" * 80 + "\n")

    return topic_map

def organize_books():
    """Main interactive organization loop"""
    print("\n📖 STEP 3: Organizing books\n")

    books = get_books_in_downloads()
    if not books:
        print("⚠️  No books to organize")
        return 0

    topic_map = display_topics_menu()

    # Create letter mapping for books
    book_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    book_map = {}

    print("\n📚 Books to organize:\n")
    for i, book in enumerate(books):
        if i < len(book_letters):
            letter = book_letters[i]
            book_map[letter] = book
            print(f"   {letter}. {book.name}")
        else:
            print(f"   Too many books (max 26)")
            break

    print("\n" + "=" * 80)
    print("Enter matches: A3 B7 C14 D0 (book_letter + topic_number)")
    print("Example: A15 = Move book A to topic 15")
    print("         B0 = Skip book B (don't move)")
    print("=" * 80 + "\n")

    matches_input = input("Enter matches: ").strip().upper()
    matches = matches_input.split()

    moved_count = 0
    skipped_count = 0

    for match in matches:
        if len(match) < 2:
            print(f"⚠️  Invalid match: {match}")
            continue

        letter = match[0]
        try:
            topic_num = int(match[1:])
        except ValueError:
            print(f"⚠️  Invalid match: {match}")
            continue

        if letter not in book_map:
            print(f"⚠️  Invalid book letter: {letter}")
            continue

        book_path = book_map[letter]

        if topic_num == 0:
            print(f"⏭️  Skipping: {book_path.name}")
            skipped_count += 1
            continue

        if topic_num not in topic_map:
            print(f"⚠️  Invalid topic number: {topic_num}")
            continue

        folder_path = topic_map[topic_num]
        dest_folder = BOOKS_PATH / folder_path
        dest_path = dest_folder / book_path.name

        # Create folder if doesn't exist
        dest_folder.mkdir(parents=True, exist_ok=True)

        if dest_path.exists():
            print(f"⚠️  File already exists: {dest_path}")
            response = input(f"   Overwrite? (y/N): ").lower().strip()
            if response not in ['y', 'yes']:
                print(f"   Skipped: {book_path.name}")
                skipped_count += 1
                continue

        try:
            shutil.move(str(book_path), str(dest_path))
            print(f"✅ {letter}. {book_path.name}")
            print(f"   → {folder_path}/")
            moved_count += 1
        except Exception as e:
            print(f"❌ Error moving {book_path.name}: {e}")

    return moved_count, skipped_count

def main():
    print("📚 Organize Books - Interactive Workflow\n")
    print("=" * 80)

    # Check if metadata exists
    if not METADATA_FILE.exists():
        print(f"❌ Metadata file not found: {METADATA_FILE}")
        return

    # STEP 1: Rename
    book_count = rename_downloads()

    if book_count == 0:
        return

    # STEP 2: Open Finder and pause
    print("\n" + "=" * 80)
    print("📂 STEP 2: Opening Finder for manual editing\n")
    subprocess.run(['open', str(DOWNLOADS_FOLDER)])

    input("\n⏸️  Review and edit book names in Finder.\n   Press ENTER to continue...")

    # STEP 3: Organize
    print("\n" + "=" * 80)
    moved, skipped = organize_books()

    print("\n" + "=" * 80)
    print(f"\n✨ Complete!")
    print(f"   📦 Moved: {moved} book(s)")
    print(f"   ⏭️  Skipped: {skipped} book(s)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
