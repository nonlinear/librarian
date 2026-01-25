

"""
This script automates the extraction and organization of your Instagram saved posts (reels and regular posts):

- Logs into Instagram using credentials from .env or command line.
- Navigates to your 'all-posts' saved group.
- Scrolls to load up to 100 saved posts.
- Extracts post links, hashtags, and title from each post (using the first comment/caption).
- Saves the results to a markdown file with #untag marker (append if exists, create if not).
- The #untag marker signals that posts still need to be removed from Instagram saved.

Dependencies:
    - undetected-chromedriver
    - selenium
    - python-dotenv

To install:
    pip install undetected-chromedriver selenium python-dotenv

TO USE:
    /opt/homebrew/bin/python3.11 .github/scripts/instagram_reels_scrape.py
    # or, if python is in your PATH:
    python3 .github/scripts/instagram_reels_scrape.py
"""


import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
from dotenv import load_dotenv
import os
import random
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import shared login function
from login import login_to_instagram

# Load .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

SAVED_URL = "https://www.instagram.com/nonlinear/saved/"


# Pergunta no terminal o caminho do arquivo de saída
# Script is in .github/scripts/instagram/, so go up 3 levels to workspace root
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
default_output = os.getenv('IG_SCRAPE_OUTPUT_PATH') or os.path.join(workspace_root, "links/reels.md")
output_path = input(f"Enter output file path (default: {default_output}): ").strip() or default_output
OUTPUT_FILE = output_path
SCRAPE_COUNT = int(os.getenv('IG_SCRAPE_COUNT', 10))

try:
    # Login to Instagram using shared function
    browser = login_to_instagram()

    print(f"[1/5] Acessando página de salvos: {SAVED_URL}")
    browser.get(SAVED_URL)
    time.sleep(5)

    # Encontrar todos os grupos de salvos
    print("[2/5] Buscando grupos de salvos...")
    group_links = browser.find_elements(By.CSS_SELECTOR, 'a[href^="/nonlinear/saved/"]')
    group_names = []
    group_hrefs = []
    for el in group_links:
        name = el.text.strip()
        href = el.get_attribute("href")
        if name and href and not href.endswith("all-posts/"):
            group_names.append(name)
            group_hrefs.append(href)

    if not group_names:
        print("Nenhum grupo encontrado além de All posts.")
        browser.quit()
        sys.exit(1)

    print("\nGrupos encontrados:")
    for idx, name in enumerate(group_names, 1):
        print(f"  [{idx}] {name}")
    while True:
        try:
            group_idx = int(input("\nDigite o número do grupo desejado: "))
            if 1 <= group_idx <= len(group_names):
                break
            else:
                print("Número inválido.")
        except Exception:
            print("Entrada inválida.")
    GROUP_NAME = group_names[group_idx-1].replace(" ", "-").lower()
    GROUP_URL = group_hrefs[group_idx-1]
    print(f"[3/5] Entrando no grupo: {GROUP_NAME} ({GROUP_URL})")
    browser.get(GROUP_URL)
    time.sleep(5)

    while True:
        try:
            user_count = int(input(f"Quantos links deseja coletar deste grupo? (padrão {SCRAPE_COUNT}): ") or SCRAPE_COUNT)
            if user_count > 0:
                break
            else:
                print("Digite um número positivo.")
        except Exception:
            print("Entrada inválida.")
    print(f"[4/5] Coletando os {user_count} primeiros links do grupo...")
    for _ in range(5):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.0, 2.0))

    elements = browser.find_elements(By.CSS_SELECTOR, 'a._a6hd')
    links = []
    for el in elements:
        href = el.get_attribute("href")
        if href and ("/reel/" in href or "/p/" in href):
            links.append(href)
        if len(links) >= user_count:
            break
    print(f"[5/5] {len(links)} links encontrados para processar.")


    import re
    results = []
    for idx, link in enumerate(links, 1):
        print(f"  [{idx}/{len(links)}] Processing: {link}")
        browser.get(link)
        time.sleep(random.uniform(2.0, 4.0))
        title = None
        hashtags = []
        caption = None

        try:
            # Try robust selector for first comment/caption
            # 1. Try new Instagram structure (main comment block)
            comments_block = WebDriverWait(browser, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x9f619.x78zum5.xdt5ytf.x5yr21d.xexx8yu.xv54qhq.x1190r2v.xf7dkkf.x10l6tqk.xh8yej3'))
            )
            # Try to get the first comment/caption (author)
            try:
                first_comment = comments_block.find_element(By.CSS_SELECTOR, 'span')
                caption = first_comment.text
            except Exception:
                pass
        except Exception:
            pass
        # Fallback: legacy selector (old Instagram layout)
        if not caption:
            try:
                legacy_caption = browser.find_element(By.XPATH, '//div[contains(@class,"C4VMK")]/span')
                caption = legacy_caption.text
            except Exception:
                caption = None
        if caption:
            hashtags = re.findall(r"#\w+", caption)
            title = caption.split('\n')[0]

        # Build tag list
        tags = [f"#{GROUP_NAME}"] + hashtags + ["#untag"]

        # If no title extracted, mark with #enrich for later enrichment
        if not title:
            title = "(no title)"
            tags.append("#enrich")

        tag_str = " ".join(tags)
        results.append(f"- [{title}]({link}) {tag_str}")

    # Append or create file (safely)
    import tempfile
    if os.path.exists(OUTPUT_FILE):
        # Append mode: read existing, add new, write to temp, then replace
        with open(OUTPUT_FILE, 'r') as f:
            existing_lines = [line.rstrip() for line in f]
        all_lines = existing_lines + results
    else:
        all_lines = results

    temp_fd, temp_path = tempfile.mkstemp(suffix='.md', text=True)
    try:
        with os.fdopen(temp_fd, 'w') as f:
            for line in all_lines:
                f.write(line + "\n")
        os.replace(temp_path, OUTPUT_FILE)
        print(f"✓ Complete! {len(results)} links written to {OUTPUT_FILE}")
    except Exception as e:
        os.unlink(temp_path)
        print(f"✗ Error saving file: {e}")
        raise

finally:
    browser.quit()
