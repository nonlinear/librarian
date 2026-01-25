#!/usr/bin/env python3
"""
Detect and crop non-square images to square (center crop).
"""
from pathlib import Path
from PIL import Image

ILLOS_DIR = Path(__file__).parent.parent.parent / "static" / "images" / "illos"

def is_square(img):
    """Check if image is square"""
    return img.width == img.height

def crop_to_square(img):
    """Center crop image to square"""
    width, height = img.size

    if width == height:
        return img

    # Use the smaller dimension as the square size
    size = min(width, height)

    # Calculate crop box (center crop)
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size

    return img.crop((left, top, right, bottom))

def main():
    jpg_files = list(ILLOS_DIR.glob("*.jpg"))

    if not jpg_files:
        print("No JPG files found in", ILLOS_DIR)
        return

    non_square = []

    # First pass: detect non-square images
    print("🔍 Scanning for non-square images...\n")
    for jpg_path in jpg_files:
        img = Image.open(jpg_path)
        if not is_square(img):
            non_square.append((jpg_path, img.width, img.height))

    if not non_square:
        print("✅ All images are already square!")
        return

    print(f"Found {len(non_square)} non-square image(s):\n")
    for path, w, h in non_square:
        print(f"  {path.name}: {w}x{h}")

    # Ask for confirmation
    response = input(f"\n⚠️  Crop these {len(non_square)} image(s) to square? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    # Second pass: crop images
    print("\n✂️  Cropping images...\n")
    for jpg_path, w, h in non_square:
        img = Image.open(jpg_path)
        cropped = crop_to_square(img)
        cropped.save(jpg_path, quality=95)
        print(f"  ✅ {jpg_path.name}: {w}x{h} → {cropped.width}x{cropped.height}")

    print(f"\n✨ Cropped {len(non_square)} image(s) to square")

if __name__ == "__main__":
    main()
