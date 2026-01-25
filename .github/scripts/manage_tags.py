"""
Manage Tags Across All Links

This script:
- Scans all .md files in links/ folder
- Detects similar hashtags (case variations, plurals, hyphens) and suggests merges
- Detects child tags and suggests adding parent tags for hierarchy
- Replaces all selected tags with the canonical tag across all files
- Removes duplicate tags on same line

Usage:
    python3.11 .github/scripts/manage_tags.py
"""

import os
import re
from collections import Counter, defaultdict

# Paths
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LINKS_DIR = os.path.join(WORKSPACE_ROOT, 'links')

# Tags to ignore (system/metadata tags)
IGNORE_TAGS = ['#untag', '#enrich', '#en-US', '#pt-BR', '#es-ES', '#ja-JP', '#ko-KR',
               '#zh-CN', '#zh-TW', '#ar-SA', '#ru-RU', '#fr-FR', '#de-DE', '#it-IT']

def is_date_tag(tag):
    """Check if tag looks like a date (#2025-12-30)."""
    return bool(re.match(r'#\d{4}-\d{2}-\d{2}', tag))

def extract_hashtags(line):
    """Extract all hashtags from a line."""
    return re.findall(r'#[\w\-]+', line)

def get_all_md_files():
    """Get all .md files in links directory."""
    if not os.path.exists(LINKS_DIR):
        return []

    files = []
    for filename in os.listdir(LINKS_DIR):
        if filename.endswith('.md'):
            files.append(os.path.join(LINKS_DIR, filename))
    return sorted(files)

def get_tag_counts_from_files(files):
    """Count all hashtags across all files (excluding system tags and dates)."""
    tag_counter = Counter()

    for filepath in files:
        with open(filepath, 'r') as f:
            for line in f:
                tags = extract_hashtags(line.strip())
                for tag in tags:
                    if tag not in IGNORE_TAGS and not is_date_tag(tag):
                        tag_counter[tag] += 1

    return tag_counter

def normalize_tag(tag):
    """Normalize tag for similarity comparison."""
    # Remove #, convert to lowercase, remove hyphens/underscores
    normalized = tag.lower().replace('#', '').replace('-', '').replace('_', '')
    # Remove common plural 's'
    if normalized.endswith('s') and len(normalized) > 3:
        normalized = normalized[:-1]
    return normalized

def find_similar_tags(tag_counts):
    """Group similar tags together."""
    # Group tags by normalized form
    groups = defaultdict(list)

    for tag, count in tag_counts.items():
        norm = normalize_tag(tag)
        groups[norm].append((tag, count))

    # Only return groups with multiple variations
    similar_groups = []
    for norm, tags in groups.items():
        if len(tags) > 1:
            # Sort by count (descending), then alphabetically
            # Prefer tags with hyphens, then lowercase, then as-is
            sorted_tags = sorted(tags, key=lambda x: (-x[1], '-' not in x[0], x[0].lower()))
            similar_groups.append([tag for tag, count in sorted_tags])

    # Sort groups by total count
    similar_groups.sort(key=lambda g: sum(tag_counts[t] for t in g), reverse=True)

    return similar_groups

def extract_parent_tag(tag):
    """Extract parent tag from a child tag.

    Examples:
        #3D-printing → #3D
        #ai-tools → #ai
        #cosplaytutorial → #cosplay
    """
    # Remove #
    tag_name = tag[1:]

    # Split by hyphen or underscore
    if '-' in tag_name:
        parent = tag_name.split('-')[0]
        return f'#{parent}'
    elif '_' in tag_name:
        parent = tag_name.split('_')[0]
        return f'#{parent}'

    # For compound words without separator, use common prefixes
    common_prefixes = ['ai', 'cosplay', '3d', '3D', 'video', 'audio', 'crypto']
    tag_lower = tag_name.lower()

    for prefix in common_prefixes:
        if tag_lower.startswith(prefix.lower()) and len(tag_name) > len(prefix):
            return f'#{prefix}'

    return None

def find_parent_child_relationships(all_tags):
    """Find all parent-child tag relationships."""
    relationships = defaultdict(set)  # parent -> set of children

    for tag in all_tags:
        if tag in IGNORE_TAGS or is_date_tag(tag):
            continue

        parent = extract_parent_tag(tag)
        if parent and parent != tag:
            relationships[parent].add(tag)

    return relationships

def replace_tags_in_line(line, tag_map):
    """Replace tags in a line according to tag_map and remove duplicates."""
    # Extract all tags from the line
    tags_in_line = extract_hashtags(line)

    # Build replacement map for this line
    replacements = {}
    for tag in tags_in_line:
        if tag in tag_map:
            replacements[tag] = tag_map[tag]

    # Apply replacements
    new_line = line
    for old_tag, new_tag in replacements.items():
        # Use word boundary to avoid partial matches
        new_line = re.sub(r'\b' + re.escape(old_tag) + r'\b', new_tag, new_line)

    # Remove duplicate tags
    # Extract all tags again after replacement
    tags_after = extract_hashtags(new_line)
    seen = set()
    final_tags = []
    for tag in tags_after:
        if tag not in seen:
            seen.add(tag)
            final_tags.append(tag)

    # Only rebuild line if we found duplicates
    if len(final_tags) < len(tags_after):
        # Split line into before-tags and tags parts
        # Find where tags start (after the URL and author)
        match = re.search(r'(\].*?\)(?:\s+by\s+\[@\w+\]\([^)]+\))?\s+)(#.+)$', new_line)
        if match:
            prefix = match.group(1)
            new_line = prefix + ' '.join(final_tags)

    return new_line

def process_files(files, tag_map):
    """Process all files and replace tags."""
    total_replacements = 0

    for filepath in files:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        modified = False
        new_lines = []

        for line in lines:
            new_line = replace_tags_in_line(line, tag_map)
            new_lines.append(new_line)
            if new_line != line:
                modified = True
                total_replacements += 1

        if modified:
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
            filename = os.path.basename(filepath)
            print(f"  ✓ Updated {filename}")

    return total_replacements

def add_parent_tags_to_line(line, parent_map):
    """Add missing parent tags to a line."""
    tags_in_line = extract_hashtags(line)
    tags_to_add = set()

    for tag in tags_in_line:
        # Find all parents for this tag
        for parent, children in parent_map.items():
            if tag in children and parent not in tags_in_line:
                tags_to_add.add(parent)

    if not tags_to_add:
        return line

    # Add parent tags after the existing tags
    # Find where tags section ends
    match = re.search(r'(\].*?\)(?:\s+by\s+\[@\w+\]\([^)]+\))?\s+)(#.+)$', line)
    if match:
        prefix = match.group(1)
        existing_tags = match.group(2)

        # Insert parent tags at the beginning of tag section (after lang/date)
        all_tags = extract_hashtags(existing_tags)

        # Separate into: lang, date, new parents, everything else
        lang_tags = [t for t in all_tags if t in IGNORE_TAGS]
        date_tags = [t for t in all_tags if is_date_tag(t)]
        other_tags = [t for t in all_tags if t not in lang_tags and t not in date_tags]

        # Build new tag order: lang, date, parents, others
        new_tags = lang_tags + date_tags + sorted(list(tags_to_add)) + other_tags

        return prefix + ' '.join(new_tags) + '\n'

    return line

def process_parent_tags(files, parent_map):
    """Process all files and add parent tags."""
    total_additions = 0

    for filepath in files:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        modified = False
        new_lines = []

        for line in lines:
            new_line = add_parent_tags_to_line(line, parent_map)
            new_lines.append(new_line)
            if new_line != line:
                modified = True
                total_additions += 1

        if modified:
            with open(filepath, 'w') as f:
                f.writelines(new_lines)
            filename = os.path.basename(filepath)
            print(f"  ✓ Updated {filename}")

    return total_additions

def main():
    print("🏷️  Tag Manager (Merge Similar + Add Hierarchy)\n")

    # Get all markdown files
    files = get_all_md_files()
    if not files:
        print("No markdown files found in links/")
        return

    print(f"Scanning {len(files)} files in links/\n")

    # ==================== STEP 1: Merge Similar Tags ====================
    print("=" * 60)
    print("STEP 1: MERGE SIMILAR TAGS")
    print("=" * 60 + "\n")

    # Get tag counts
    tag_counts = get_tag_counts_from_files(files)

    if not tag_counts:
        print("No tags found")
        step1_applied = False
    else:
        # Find similar tags
        similar_groups = find_similar_tags(tag_counts)

        if not similar_groups:
            print("No similar tags detected!")
            step1_applied = False
        else:
            print(f"Found {len(similar_groups)} groups of similar tags:\n")

            # Show suggestions and get user approval
            tag_map = {}
            approved_count = 0

            for idx, group in enumerate(similar_groups, 1):
                canonical = group[0]
                others = group[1:]

                # Show counts for context
                counts_str = ' + '.join([f"{tag}({tag_counts[tag]})" for tag in group])

                print(f"{idx}. Merge: {', '.join(others)} → {canonical}")
                print(f"   ({counts_str})")

                response = input("   Approve? (y/n/q to quit): ").lower().strip()

                if response == 'q':
                    print("\nStopped by user")
                    break
                elif response == 'y':
                    for tag in others:
                        tag_map[tag] = canonical
                    approved_count += 1
                    print("   ✓ Approved\n")
                else:
                    print("   ✗ Skipped\n")

            if not tag_map:
                print("No merges approved")
                step1_applied = False
            else:
                print(f"\nApproved {approved_count} merge groups")
                print(f"Total tags to merge: {len(tag_map)}\n")

                confirm = input("Apply all approved merges? (y/n): ").lower().strip()
                if confirm != 'y':
                    print("Cancelled Step 1")
                    step1_applied = False
                else:
                    # Process files
                    print("\nProcessing files...")
                    replacements = process_files(files, tag_map)

                    print(f"\n✓ Step 1 Complete!")
                    print(f"  Modified {replacements} lines across {len(files)} files\n")
                    step1_applied = True

    # ==================== STEP 2: Add Parent Tags ====================
    print("\n" + "=" * 60)
    print("STEP 2: ADD PARENT TAGS (HIERARCHY)")
    print("=" * 60 + "\n")

    proceed = input("Continue to parent tag hierarchy? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Skipped Step 2")
        print("\n✓ Tag management complete!")
        return

    # Collect all unique tags (re-scan after merges)
    all_tags = set()
    for filepath in files:
        with open(filepath, 'r') as f:
            for line in f:
                tags = extract_hashtags(line.strip())
                all_tags.update(tags)

    # Find parent-child relationships
    relationships = find_parent_child_relationships(all_tags)

    if not relationships:
        print("No parent-child tag relationships detected!")
        print("\n✓ Tag management complete!")
        return

    print(f"Found {len(relationships)} parent tags:\n")

    # Show suggestions and get approval
    parent_map = {}
    approved_count = 0

    for parent, children in sorted(relationships.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Parent: {parent}")
        print(f"  Children: {', '.join(sorted(children))}")
        print(f"  ({len(children)} tags will gain parent {parent})")

        response = input("  Add parent tag? (y/n/q to quit): ").lower().strip()

        if response == 'q':
            print("\nStopped by user")
            break
        elif response == 'y':
            parent_map[parent] = children
            approved_count += 1
            print("  ✓ Approved\n")
        else:
            print("  ✗ Skipped\n")

    if not parent_map:
        print("No parent tags approved")
        print("\n✓ Tag management complete!")
        return

    print(f"\nApproved {approved_count} parent tags")

    confirm = input("\nApply parent tags? (y/n): ").lower().strip()
    if confirm != 'y':
        print("Cancelled Step 2")
        print("\n✓ Tag management complete!")
        return

    # Process files
    print("\nProcessing files...")
    additions = process_parent_tags(files, parent_map)

    print(f"\n✓ Step 2 Complete!")
    print(f"  Added parent tags to {additions} lines across {len(files)} files")

    print("\n✓ Tag management complete!")

if __name__ == "__main__":
    main()
