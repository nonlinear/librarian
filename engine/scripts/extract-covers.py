#!/usr/bin/env python3
"""
Extract cover images from EPUB files.
Saves to same directory as epub: book.epub → book.jpg
"""

import zipfile
import json
from pathlib import Path
import sys

def extract_epub_cover(epub_path: Path, output_dir: Path) -> str | None:
    """Extract cover from EPUB. Returns output path if successful."""
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            # Common cover locations in EPUBs
            cover_paths = [
                'OEBPS/Images/cover.jpg',
                'OEBPS/Images/cover.png',
                'EPUB/images/cover.jpg',
                'EPUB/images/cover.png',
                'images/cover.jpg',
                'images/cover.png',
            ]
            
            # Try exact paths first
            for cover_path in cover_paths:
                if cover_path in z.namelist():
                    output_file = output_dir / f"{epub_path.stem}.jpg"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with z.open(cover_path) as source:
                        output_file.write_bytes(source.read())
                    
                    print(f"✓ {epub_path.name} → {output_file}")
                    return str(output_file)
            
            # Fallback: search for any file with 'cover' in name
            for name in z.namelist():
                if 'cover' in name.lower() and name.endswith(('.jpg', '.jpeg', '.png')):
                    output_file = output_dir / f"{epub_path.stem}.{name.split('.')[-1]}"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with z.open(name) as source:
                        output_file.write_bytes(source.read())
                    
                    print(f"✓ {epub_path.name} → {output_file}")
                    return str(output_file)
            
            print(f"✗ {epub_path.name} - no cover found")
            return None
            
    except Exception as e:
        print(f"✗ {epub_path.name} - error: {e}")
        return None

def main():
    books_dir = Path('books')
    
    if not books_dir.exists():
        print("Error: books/ directory not found")
        sys.exit(1)
    
    # Find all EPUBs
    epubs = list(books_dir.rglob('*.epub'))
    print(f"Found {len(epubs)} EPUB files\n")
    
    success = 0
    failed = 0
    
    for epub_path in epubs:
        # Output to same directory as epub (book.epub → book.jpg)
        topic_dir = epub_path.parent
        
        result = extract_epub_cover(epub_path, topic_dir)
        
        if result:
            success += 1
        else:
            failed += 1
    
    print(f"\n✓ {success} covers extracted")
    print(f"✗ {failed} failed")

if __name__ == '__main__':
    main()
