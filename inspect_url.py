import argparse
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager


def get_page_content(url: str, save_content: bool = False) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # options.set_preference("intl.accept_languages", "hu-HU,hu")
    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(),
        options=options,
    )

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
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source
        if save_content:
            with open("inspect_url.html", "w") as f:
                f.write(page_source)
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
