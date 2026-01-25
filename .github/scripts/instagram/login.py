"""
Shared Instagram login functionality for automation scripts.

Provides a reusable login flow:
1. Opens visible browser for manual login
2. Transfers session cookies to headless browser
3. Returns authenticated headless browser instance

Dependencies:
    - undetected-chromedriver
"""

import undetected_chromedriver as uc
import random


def login_to_instagram():
    """
    Open browser for manual login, then transfer to headless browser.

    Returns:
        Browser instance (headless) with logged-in Instagram session
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    ]

    print("[1/2] Opening browser for manual Instagram login...")

    # Step 1: Visible browser for manual login
    visible_options = uc.ChromeOptions()
    visible_options.add_argument("--disable-gpu")
    visible_options.add_argument("--window-size=1920,1080")
    visible_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    visible_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    visible_browser = uc.Chrome(options=visible_options)
    visible_browser.get("https://www.instagram.com/accounts/login/")

    input("After logging in manually, press Enter here to continue...")

    # Step 2: Transfer cookies to headless browser
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

    # First, navigate to Instagram's base URL
    headless_browser.get("https://www.instagram.com/")

    # Then add cookies from the visible browser session
    for cookie in cookies:
        try:
            headless_browser.add_cookie(cookie)
        except Exception:
            pass  # Some cookies may fail to add, that's okay

    # Refresh to apply cookies
    headless_browser.refresh()

    print("✓ Login complete. Browser ready.\n")

    return headless_browser
