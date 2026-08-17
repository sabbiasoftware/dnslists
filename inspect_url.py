import argparse
import hashlib
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth


def _find_binary(*candidates: str) -> str | None:
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _wait_for_dom_stability(driver, max_wait=60, poll=0.5, stable_for=3.0):
    prev = None
    stable = 0.0
    deadline = time.time() + max_wait
    while time.time() < deadline:
        h = hashlib.md5(driver.page_source.encode()).hexdigest()
        if h == prev:
            stable += poll
            if stable >= stable_for:
                return
        else:
            stable = 0.0
            prev = h
        time.sleep(poll)


def get_page_content(url: str, debug: bool = False) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    options = webdriver.ChromeOptions()
    if not debug:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    chromium_binary = _find_binary("/usr/bin/chromium", "/usr/bin/chromium-browser")
    if chromium_binary:
        options.binary_location = chromium_binary

    chromedriver_path = _find_binary(
        "/usr/bin/chromedriver", "/usr/lib/chromium-browser/chromedriver"
    )
    service = (
        Service(executable_path=chromedriver_path) if chromedriver_path else Service()
    )

    driver = webdriver.Chrome(service=service, options=options)

    stealth(
        driver,
        languages=["hu-HU", "hu"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    try:
        driver.get(url)
        _wait_for_dom_stability(driver)
        page_source = driver.page_source
        if debug:
            with open("inspect_url.html", "w") as f:
                f.write(page_source)
            driver.save_screenshot("inspect_url.png")
        return page_source
    finally:
        driver.quit()


def count_pattern_occurrences(pattern: str, text: str) -> int:
    escaped = re.escape(pattern)
    regex = (
        rf"(?<![a-zA-Z0-9áéíóöőúüűÁÉÍÓÖŐÚÜŰ]){escaped}(?![a-zA-Z0-9áéíóöőúüűÁÉÍÓÖŐÚÜŰ])"
    )
    return len(re.findall(regex, text, re.IGNORECASE))


def count_keyword_occurrences(text: str) -> dict[str, int]:
    with open("webshopkeywords", "r") as f:
        patterns = [line.strip() for line in f if line.strip()]
    return {pattern: count_pattern_occurrences(pattern, text) for pattern in patterns}


def format_occurrences(occurrences: dict[str, int]) -> str:
    sorted_items = sorted(occurrences.items(), key=lambda x: x[1], reverse=True)
    if not sorted_items:
        return ""
    max_count = max(occurrences.values())
    width = len(str(max_count)) if max_count > 0 else 0
    lines = [f'{count:{width}d}: "{pattern}"' for pattern, count in sorted_items]
    return "\n".join(lines)


def inspect_url(url: str) -> str:
    return format_occurrences(count_keyword_occurrences(get_page_content(url)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to scrape")
    args = parser.parse_args()
    content = get_page_content(args.url, True)
    print(format_occurrences(count_keyword_occurrences(content)))
