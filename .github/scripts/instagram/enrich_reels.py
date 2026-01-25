"""
Enrich Instagram reels markdown file with titles and hashtags.

This script:
- Reads a markdown file with Instagram post links
- Identifies posts that need enrichment (missing title or minimal tags)
- Logs into Instagram and visits each post
- Extracts title (first line of caption) and hashtags
- Updates the markdown file with enriched data

Dependencies:
    - undetected-chromedriver
    - selenium
    - python-dotenv

TO USE:
    python3.11 .github/scripts/instagram/enrich_reels.py
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
import random
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

# Import shared login function
from login import login_to_instagram

# Tags to ignore when counting (will grow over time)
IGNORE_TAGS = ['#untag', '#enrich']

# Validation: Known correct author mappings for debugging
KNOWN_AUTHORS = {
    'DS4YY6nEReK': 'the_smart_cookies_pod',  # Should extract first, ignore "and chrishardingjapan"
    'DSffPF3AJuX': 'lexlos3r',
    'DSJChIzjJCc': 'icl.noticias',  # Should ignore "and 3 others"
    'DSBvz9oDB4F': 'eddysilvv',
    'DSDdFeIiRg6': 'alvarohenriqueguitar',
}

def extract_url(line):
    """Extract Instagram URL from markdown line."""
    m = re.search(r'(https://www\.instagram\.com/[\w\-/]+)', line)
    return m.group(1) if m else None

def extract_title_from_line(line):
    """Extract title from markdown link format."""
    m = re.search(r'\[([^\]]+)\]', line)
    if m:
        title = m.group(1)
        return None if title == "(no title)" else title
    return None

def extract_hashtags_from_line(line):
    """Extract all hashtags from line, excluding ignored ones."""
    all_tags = re.findall(r"#\w+", line)
    return [tag for tag in all_tags if tag not in IGNORE_TAGS]

def extract_caption_title(caption_text):
    """
    Generate smart, concise title from caption.

    AI-style approach:
    - Extract first meaningful sentence
    - Remove filler words
    - Keep 5-7 key words for better context
    - Fallback to hashtag synthesis
    """
    if not caption_text:
        return None

    # Split into lines, skip first line (username)
    lines = caption_text.split('\n')
    if len(lines) > 1:
        text_part = ' '.join(lines[1:])
    else:
        text_part = caption_text

    # Find where hashtags start
    hashtag_start = text_part.find('#')

    # Extract text before hashtags
    if hashtag_start > 0:
        text_part = text_part[:hashtag_start].strip()
        # Clean up noise
        text_part = re.sub(r'\b\d+[wdmh]\b', '', text_part)
        text_part = re.sub(r'\bEdited\b', '', text_part, flags=re.IGNORECASE)
        text_part = re.sub(r'[•\n]+', ' ', text_part)
        text_part = text_part.strip()

        if text_part and len(text_part) > 3:
            # Get first sentence or chunk
            sentences = re.split(r'[.!?]', text_part)
            first_sentence = sentences[0].strip() if sentences else text_part

            # Remove common filler words for better semantic value
            filler_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
            words = first_sentence.split()
            meaningful_words = [w for w in words if w.lower() not in filler_words or len(words) <= 5]

            # Take 5-7 meaningful words (better context)
            if len(meaningful_words) >= 7:
                return ' '.join(meaningful_words[:7])
            elif len(meaningful_words) >= 5:
                return ' '.join(meaningful_words[:5])
            else:
                return ' '.join(meaningful_words)

    # Fallback: use first 3 hashtags
    hashtags = re.findall(r"#(\w+)", caption_text)
    if hashtags:
        return ' '.join(hashtags[:3])

def extract_caption_hashtags(caption_text):
    """Extract hashtags from caption text."""
    if not caption_text:
        return []
    return re.findall(r"#\w+", caption_text)

def extract_post_date(browser):
    """Extract publication date from Instagram post."""
    try:
        # Look for timestamp element (time tag or datetime attribute)
        time_elements = browser.find_elements(By.TAG_NAME, 'time')
        if time_elements:
            datetime_str = time_elements[0].get_attribute('datetime')
            if datetime_str:
                # Parse ISO format: 2025-01-15T12:34:56.000Z
                date_part = datetime_str.split('T')[0]  # Get YYYY-MM-DD
                return f'#{date_part}'
    except Exception:
        pass
    return None

def extract_author_username(caption_text):
    """
    Extract author username from caption text.

    Instagram captions start with:
    username (or "username and username2" for collabs)
    timestamp
    actual text...

    Extract only the FIRST username, ignore collaborators.
    """
    if not caption_text:
        return None

    try:
        lines = caption_text.split('\n')
        if lines:
            # First line is usually the username(s)
            username_line = lines[0].strip()

            # Skip timestamps (like "3w", "Edited")
            if re.match(r'^\d+[wdmh]$', username_line) or username_line.lower() == 'edited':
                return None

            # Handle collaborations: "user1 and user2" → take first
            if ' and ' in username_line:
                username = username_line.split(' and ')[0].strip()
            else:
                username = username_line

            if username:
                print(f"    Extracted author: @{username}")
                return f'@{username}'
    except Exception as e:
        print(f"    Author extraction error: {e}")

    return None

def detect_language(caption_text):
    """Detect language from caption text and return locale tag."""
    if not caption_text or len(caption_text.strip()) < 10:
        return None

    try:
        # Detect base language code
        lang_code = detect(caption_text)

        # Map to locale tags
        locale_map = {
            'en': '#en-US',
            'pt': '#pt-BR',
            'es': '#es-ES',
            'fr': '#fr-FR',
            'de': '#de-DE',
            'it': '#it-IT',
            'ja': '#ja-JP',
            'ko': '#ko-KR',
            'zh-cn': '#zh-CN',
            'zh-tw': '#zh-TW',
            'ar': '#ar-SA',
            'ru': '#ru-RU',
        }

        return locale_map.get(lang_code, f'#{lang_code}')

    except LangDetectException:
        return None

def extract_caption_hashtags_original(caption_text):
    """Extract hashtags from caption text (without language detection)."""
    if not caption_text:
        return []
    return re.findall(r"#\w+", caption_text)

def needs_enrichment(line):
    """
    Determine if a line needs enrichment.

    Simple rule: if post has #enrich, enrich it.
    """
    return '#enrich' in line

def scrape_post_data(browser, url):
    """
    Visit Instagram post and extract caption, title, and hashtags.

    Strategy:
    1. Find all text spans with hashtags
    2. Pick the longest one (likely the author's caption)
    3. Extract title and hashtags from it

    Returns:
        tuple: (title, hashtags, language, post_date, author)
    """
    browser.get(url)
    time.sleep(random.uniform(2.0, 4.0))

    caption = None

    # Extract post ID for validation
    post_id_match = re.search(r'/p/([^/]+)/', url)
    post_id = post_id_match.group(1) if post_id_match else None

    try:
        # Wait for page to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "span"))
        )

        # Find all comment spans
        comment_spans = browser.find_elements(
            By.CSS_SELECTOR,
            'span.x1lliihq.x1plvlek.xryxfnj[dir="auto"]'
        )

        # Find all spans with hashtags, pick the longest (likely the caption)
        candidates = []
        for span in comment_spans:
            text = span.text.strip()
            if text and '#' in text and len(text) > 10:
                # Filter out text that's ONLY hashtags
                if not text.startswith('#'):
                    candidates.append(text)

        # Pick the longest text (real captions are longer than just hashtag lists)
        if candidates:
            caption = max(candidates, key=len)
            print(f"    Found caption: {caption[:80]}...")
        else:
            print(f"    No caption with hashtags found")

    except Exception as e:
        print(f"    Caption extraction error: {e}")
        pass

    # Extract date from browser, author from caption
    post_date = extract_post_date(browser)
    author = extract_author_username(caption)

    # Fallback: Extract author from page metadata if caption doesn't have it
    if not author:
        try:
            # Find the twitter:title meta tag which contains: "Name (@username) • Instagram reel"
            meta_tag = browser.find_element(By.CSS_SELECTOR, 'meta[name="twitter:title"]')
            title_content = meta_tag.get_attribute('content')
            # Extract username from "Name (@username) • Instagram"
            match = re.search(r'\(@([^)]+)\)', title_content)
            if match:
                author = f"@{match.group(1)}"
                print(f"    Extracted author from metadata: {author}")
        except Exception as e:
            print(f"    Could not extract author from metadata: {e}")

    # VALIDATION: Check if this is a known post
    if post_id and post_id in KNOWN_AUTHORS:
        expected_username = KNOWN_AUTHORS[post_id]
        extracted_username = author.replace('@', '') if author else None

        if extracted_username != expected_username:
            print(f"    ⚠️  VALIDATION FAILED!")
            print(f"    Expected: @{expected_username}")
            print(f"    Got: {author or 'None'}")

            # Try to find where the expected username appears on the page
            try:
                page_source = browser.page_source
                if expected_username in page_source:
                    # Find context around the username
                    idx = page_source.find(expected_username)
                    context_start = max(0, idx - 100)
                    context_end = min(len(page_source), idx + len(expected_username) + 100)
                    context = page_source[context_start:context_end]
                    print(f"    Found '{expected_username}' in page source:")
                    print(f"    ...{context}...")
                else:
                    print(f"    '{expected_username}' NOT found in page source!")
            except Exception as e:
                print(f"    Could not search page: {e}")

    if caption:
        title = extract_caption_title(caption)
        hashtags = extract_caption_hashtags(caption)
        language = detect_language(caption)
        return (title, hashtags, language, post_date, author)

    return (None, [], None, post_date, author)

def update_line(line, new_title=None, new_hashtags=None, author=None, language=None, post_date=None):
    """
    Update a markdown line with new title and/or hashtags.
    Preserves existing URL, group tag, and #untag marker.
    Adds #no-caption if enrichment fails.

    Tag order: @username #LANG #DATE #existing-tags #new-tags
    """
    url = extract_url(line)
    if not url:
        return line

    # Extract existing data
    existing_title = extract_title_from_line(line) or "(no title)"
    existing_tags = extract_hashtags_from_line(line)
    has_untag = '#untag' in line

    # Use new data if provided, otherwise keep existing
    final_title = new_title if new_title else existing_title

    # Build tags in specific order: @username #LANG #DATE #existing #new
    ordered_tags = []

    # 1. Author (@username)
    if author:
        ordered_tags.append(author)

    # 2. Language (#LANG)
    if language:
        ordered_tags.append(language)

    # 3. Date (#DATE)
    if post_date:
        ordered_tags.append(post_date)

    # 4. Existing tags (except metadata we're replacing)
    metadata_tags = {author, language, post_date, '#enrich'}
    for tag in existing_tags:
        if tag not in metadata_tags and tag not in IGNORE_TAGS:
            ordered_tags.append(tag)

    # 5. New hashtags from caption
    if new_hashtags:
        for tag in new_hashtags:
            if tag not in ordered_tags and tag not in IGNORE_TAGS:
                ordered_tags.append(tag)

    # Add #untag back if it was there
    if has_untag:
        ordered_tags.append('#untag')

    # If enrichment failed (no new title or hashtags), keep #enrich tag
    if not new_title and not new_hashtags:
        if '#enrich' not in ordered_tags:
            ordered_tags.append('#enrich')

    # Build the updated line
    tags_str = ' '.join(ordered_tags)
    return f"- [{final_title}]({url}) {tags_str}".strip()

# Main execution
if __name__ == "__main__":
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

    # Ask for file path
    # Script is in .github/scripts/instagram/, so go up 3 levels to workspace root
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    default_file = os.getenv('IG_SCRAPE_OUTPUT_PATH') or os.path.join(workspace_root, "links/reels.md")
    file_path = input(f"Enter file path to enrich (default: {default_file}): ").strip() or default_file

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        exit(1)

    # Read file
    with open(file_path, 'r') as f:
        lines = [line.rstrip() for line in f]

    # Filter lines that need enrichment
    lines_to_enrich = []
    for idx, line in enumerate(lines):
        if line.strip() and needs_enrichment(line):
            url = extract_url(line)
            if url:
                lines_to_enrich.append((idx, line, url))

    if not lines_to_enrich:
        print("No posts need enrichment. All posts have titles and tags!")
        exit(0)

    print(f"\nFound {len(lines_to_enrich)} posts that need enrichment:")
    for idx, line, url in lines_to_enrich[:5]:
        print(f"  - {url}")
    if len(lines_to_enrich) > 5:
        print(f"  ... and {len(lines_to_enrich) - 5} more")

    # Ask how many to process
    default_count = min(10, len(lines_to_enrich))
    while True:
        try:
            how_many = input(f"\nHow many posts to enrich? (default {default_count}, max {len(lines_to_enrich)}): ").strip()
            how_many = int(how_many) if how_many else default_count
            if 1 <= how_many <= len(lines_to_enrich):
                break
            else:
                print(f"Please enter a number between 1 and {len(lines_to_enrich)}")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Limit to requested count
    lines_to_enrich = lines_to_enrich[:how_many]

    # Login to Instagram
    browser = login_to_instagram()

    try:
        # Process each post
        updated_count = 0
        for current_idx, (idx, old_line, url) in enumerate(lines_to_enrich, 1):
            print(f"\n[{current_idx}/{len(lines_to_enrich)}] Processing: {url}")

            title, hashtags, language, post_date, author = scrape_post_data(browser, url)

            if title or hashtags or language or post_date or author:
                # Pass metadata separately for proper ordering
                new_line = update_line(old_line, title, hashtags, author, language, post_date)
                lines[idx] = new_line
                updated_count += 1

                meta_info = []
                if author:
                    meta_info.append(author)
                if language:
                    meta_info.append(language)
                if post_date:
                    meta_info.append(post_date)
                meta_str = f" [{', '.join(meta_info)}]" if meta_info else ""

                print(f"  ✓ Updated: {title or '(no title)'} + {len(hashtags)} hashtags{meta_str}")
            else:
                # Remove #enrich tag even on failure (don't clog the process)
                new_line = re.sub(r'\s*#enrich\b', '', old_line).strip()
                lines[idx] = new_line
                print(f"  ✗ Could not extract data (removed #enrich tag)")

        # Save updated file (write to temp file first, then rename for safety)
        import tempfile
        temp_fd, temp_path = tempfile.mkstemp(suffix='.md', text=True)
        try:
            with os.fdopen(temp_fd, 'w') as f:
                for line in lines:
                    f.write(line + '\n')
            # Only replace original file if write succeeded
            os.replace(temp_path, file_path)
            print(f"\n✓ Enrichment complete! Updated {updated_count}/{len(lines_to_enrich)} posts.")
            print(f"  Saved to: {file_path}")
        except Exception as e:
            os.unlink(temp_path)  # Clean up temp file
            print(f"\n✗ Error saving file: {e}")
            raise

    finally:
        browser.quit()
