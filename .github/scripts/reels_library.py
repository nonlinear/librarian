"""
Instagram Reels Library - All-in-one processor

Fully integrated workflow: scrape → enrich → untag
- Logs into Instagram once (manual login → headless automation)
- Scrapes posts from selected saved collection
- Enriches with AI titles, language, date, author, hashtags
- Removes posts from Instagram saved
- Saves to markdown with full metadata (no #enrich or #untag markers)

Dependencies:
    pip install undetected-chromedriver selenium python-dotenv langdetect

Usage:
    # From workspace root:
    python3.11 .github/scripts/reels_library.py

    # Or from .github/scripts directory:
    python3.11 reels_library.py
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import re
import random
import tempfile
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
import pyperclip

SAVED_URL = "https://www.instagram.com/nonlinear/saved/"

# ============================================================================
# LOGIN
# ============================================================================

def login_to_instagram():
    """Open browser for manual login, then transfer to headless browser."""
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    ]

    print("[1/2] Opening browser for manual Instagram login...")

    visible_options = uc.ChromeOptions()
    visible_options.add_argument("--disable-gpu")
    visible_options.add_argument("--window-size=1920,1080")
    visible_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    visible_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    visible_browser = uc.Chrome(options=visible_options)
    visible_browser.get("https://www.instagram.com/accounts/login/")

    input("After logging in manually, press Enter here to continue...")

    cookies = visible_browser.get_cookies()
    visible_browser.quit()

    print("[2/2] Transferring session to headless browser...")

    headless_options = uc.ChromeOptions()
    headless_options.add_argument("--headless")
    headless_options.add_argument("--disable-gpu")
    headless_options.add_argument("--window-size=1920,1080")
    headless_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    headless_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    headless_browser = uc.Chrome(options=headless_options)
    headless_browser.get("https://www.instagram.com/")

    for cookie in cookies:
        try:
            headless_browser.add_cookie(cookie)
        except Exception:
            pass

    headless_browser.refresh()
    print("✓ Login complete. Browser ready.\n")

    return headless_browser

# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_caption_title(caption_text):
    """Generate smart, concise title from caption (5-7 meaningful words)."""
    if not caption_text:
        return None

    lines = caption_text.split('\n')
    if len(lines) > 1:
        text_part = ' '.join(lines[1:])
    else:
        text_part = caption_text

    hashtag_start = text_part.find('#')

    if hashtag_start > 0:
        text_part = text_part[:hashtag_start].strip()
        text_part = re.sub(r'\b\d+[wdmh]\b', '', text_part)
        text_part = re.sub(r'\bEdited\b', '', text_part, flags=re.IGNORECASE)
        text_part = re.sub(r'[•\n]+', ' ', text_part)
        text_part = text_part.strip()

        if text_part and len(text_part) > 3:
            sentences = re.split(r'[.!?]', text_part)
            first_sentence = sentences[0].strip() if sentences else text_part

            filler_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
            words = first_sentence.split()
            meaningful_words = [w for w in words if w.lower() not in filler_words or len(words) <= 5]

            if len(meaningful_words) >= 7:
                return ' '.join(meaningful_words[:7])
            elif len(meaningful_words) >= 5:
                return ' '.join(meaningful_words[:5])
            else:
                return ' '.join(meaningful_words)

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
        time_elements = browser.find_elements(By.TAG_NAME, 'time')
        if time_elements:
            datetime_str = time_elements[0].get_attribute('datetime')
            if datetime_str:
                date_part = datetime_str.split('T')[0]
                return f'#{date_part}'
    except Exception:
        pass
    return None

def extract_author_username(caption_text):
    """Extract author username from caption first line."""
    if not caption_text:
        return None

    try:
        lines = caption_text.split('\n')
        if lines:
            username_line = lines[0].strip()

            if re.match(r'^\d+[wdmh]$', username_line) or username_line.lower() == 'edited':
                return None

            if ' and ' in username_line:
                username = username_line.split(' and ')[0].strip()
            else:
                username = username_line

            if username:
                return f'@{username}'
    except Exception:
        pass

    return None

def extract_author_from_metadata(browser):
    """Fallback: Extract author from page metadata."""
    try:
        meta_tag = browser.find_element(By.CSS_SELECTOR, 'meta[name="twitter:title"]')
        title_content = meta_tag.get_attribute('content')
        match = re.search(r'\(@([^)]+)\)', title_content)
        if match:
            return f"@{match.group(1)}"
    except Exception:
        pass
    return None

def detect_language(caption_text):
    """Detect language from caption text and return locale tag."""
    if not caption_text or len(caption_text.strip()) < 10:
        return None

    try:
        lang_code = detect(caption_text)
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

# ============================================================================
# SCRAPING FUNCTIONS
# ============================================================================

def get_saved_groups(browser):
    """Get list of saved collection groups."""
    print(f"[1/4] Accessing saved page: {SAVED_URL}")
    browser.get(SAVED_URL)
    time.sleep(5)

    print("[2/4] Finding saved groups...")
    group_links = browser.find_elements(By.CSS_SELECTOR, 'a[href^="/nonlinear/saved/"]')
    group_names = []
    group_hrefs = []

    for el in group_links:
        name = el.text.strip()
        href = el.get_attribute("href")
        if name and href and not href.endswith("all-posts/"):
            group_names.append(name)
            group_hrefs.append(href)

    return group_names, group_hrefs

def scrape_group_links(browser, group_url, count):
    """Scrape post links from a saved group."""
    browser.get(group_url)
    time.sleep(5)

    for _ in range(5):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.0, 2.0))

    elements = browser.find_elements(By.CSS_SELECTOR, 'a._a6hd')
    links = []
    for el in elements:
        href = el.get_attribute("href")
        if href and ("/reel/" in href or "/p/" in href):
            links.append(href)
        if len(links) >= count:
            break

    return links

# ============================================================================
# ENRICHMENT FUNCTION
# ============================================================================

def enrich_post(browser, url):
    """
    Visit post and extract all metadata.
    Returns: (title, hashtags, language, post_date, author)
    """
    browser.get(url)
    time.sleep(random.uniform(2.0, 4.0))

    caption = None

    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "span"))
        )

        comment_spans = browser.find_elements(
            By.CSS_SELECTOR,
            'span.x1lliihq.x1plvlek.xryxfnj[dir="auto"]'
        )

        candidates = []
        for span in comment_spans:
            text = span.text.strip()
            if text and '#' in text and len(text) > 10:
                if not text.startswith('#'):
                    candidates.append(text)

        if candidates:
            caption = max(candidates, key=len)
            print(f"    ✓ Caption found")
        else:
            print(f"    ⚠ No caption with hashtags")

    except Exception as e:
        print(f"    ✗ Caption error: {e}")

    post_date = extract_post_date(browser)
    author = extract_author_username(caption)

    if not author:
        author = extract_author_from_metadata(browser)
        if author:
            print(f"    ✓ Author from metadata: {author}")

    if caption:
        title = extract_caption_title(caption)
        hashtags = extract_caption_hashtags(caption)
        language = detect_language(caption)
        return (title, hashtags, language, post_date, author)

    return (None, [], None, post_date, author)

# ============================================================================
# UNTAG FUNCTION
# ============================================================================

def untag_post(browser, url):
    """Remove post from Instagram saved collection."""
    try:
        remove_button = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[aria-label="Remove"]'))
        )

        parent = remove_button.find_element(By.XPATH, '..')
        parent.click()
        time.sleep(1.5)

        try:
            WebDriverWait(browser, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[aria-label="Save"]'))
            )
            print(f"    ✓ Removed from saved")
            return True
        except TimeoutException:
            print(f"    ⚠ Could not confirm removal")
            return True

    except (TimeoutException, NoSuchElementException):
        print(f"    ⚠ Remove button not found (may be unsaved already)")
        return False
    except Exception as e:
        print(f"    ✗ Untag error: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

    # Ask for file path
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    default_file = os.getenv('IG_SCRAPE_OUTPUT_PATH') or os.path.join(workspace_root, "links/reels.md")
    file_path = input(f"Enter output file path (default: {default_file}): ").strip() or default_file

    # Login once
    browser = login_to_instagram()

    try:
        # Get saved groups
        group_names, group_hrefs = get_saved_groups(browser)

        if not group_names:
            print("No saved groups found.")
            exit(1)

        print("\nSaved groups found:")
        for idx, name in enumerate(group_names, 1):
            print(f"  [{idx}] {name}")

        # Select group
        while True:
            try:
                group_idx = int(input("\nSelect group number: "))
                if 1 <= group_idx <= len(group_names):
                    break
                else:
                    print("Invalid number.")
            except Exception:
                print("Invalid input.")

        GROUP_NAME = group_names[group_idx-1].replace(" ", "-").lower()
        GROUP_URL = group_hrefs[group_idx-1]

        # Ask how many
        default_count = 10
        while True:
            try:
                count = int(input(f"How many posts to process? (default {default_count}): ") or default_count)
                if count > 0:
                    break
                else:
                    print("Enter a positive number.")
            except Exception:
                print("Invalid input.")

        # Scrape links
        print(f"\n[3/4] Scraping {count} posts from {GROUP_NAME}...")
        links = scrape_group_links(browser, GROUP_URL, count)
        print(f"[4/4] Found {len(links)} posts to process\n")

        # Read existing file
        existing_lines = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                existing_lines = [line.rstrip() for line in f]

        # Process each post: enrich → untag → save
        new_lines = []
        for idx, link in enumerate(links, 1):
            print(f"\n[{idx}/{len(links)}] Processing: {link}")

            # Enrich
            title, hashtags, language, post_date, author = enrich_post(browser, link)

            # Untag (while still on the page)
            untag_post(browser, link)

            # Build final line (no #enrich, no #untag)
            final_title = title or "(no title)"

            # Format author as clickable link
            author_str = ""
            if author:
                username = author.replace('@', '')
                author_str = f"by [@{username}](https://www.instagram.com/{username}) "

            # Tag order: #LANG #DATE #group #hashtags
            ordered_tags = []

            if language:
                ordered_tags.append(language)
            if post_date:
                ordered_tags.append(post_date)

            ordered_tags.append(f'#{GROUP_NAME}')

            for tag in hashtags:
                if tag not in ordered_tags:
                    ordered_tags.append(tag)

            tags_str = ' '.join(ordered_tags)
            new_line = f"- [{final_title}]({link}) {author_str}{tags_str}".strip()
            new_lines.append(new_line)

            # Backup to clipboard after each successful post
            if new_lines:
                backup_content = '\n'.join(new_lines)
                try:
                    pyperclip.copy(backup_content)
                except Exception:
                    pass  # Silent fail if clipboard not available

            meta_info = []
            if author:
                meta_info.append(author)
            if language:
                meta_info.append(language)
            if post_date:
                meta_info.append(post_date)
            meta_str = f" [{', '.join(meta_info)}]" if meta_info else ""

            print(f"  ✓ Done: {final_title[:50]}... + {len(hashtags)} tags{meta_str}")

        # Combine with existing and save
        all_lines = existing_lines + new_lines

        temp_fd, temp_path = tempfile.mkstemp(suffix='.md', text=True)
        try:
            with os.fdopen(temp_fd, 'w') as f:
                for line in all_lines:
                    f.write(line + "\n")
            os.replace(temp_path, file_path)
            print(f"\n✓ Complete! Processed {len(new_lines)} posts.")
            print(f"  Saved to: {file_path}")
        except Exception as e:
            os.unlink(temp_path)
            print(f"\n✗ Error saving file: {e}")
            raise

    finally:
        browser.quit()
