
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


URL = "https://github.com/orgs/google/repositories?type=all"

headers = {
    "User-Agent": "Mozilla/5.0"
}

DB_NAME = "google_repositories.db"

def convert_stars(star_text):
    if not star_text:
        return 0

    star_text = star_text.replace(",", "").strip()

    match = re.search(r"(\d+(?:\.\d+)?)\s*([kKmM]?)", star_text)

    if match:
        number = float(match.group(1))
        unit = match.group(2).lower()

        if unit == "k":
            number *= 1000
        elif unit == "m":
            number *= 1000000

        return int(number)

    return 0


# 主要言語を取得する関数

def get_main_language(page, repo_name):

    detail_url = f"https://github.com/google/{repo_name}"

    try:
        page.goto(
            detail_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.wait_for_selector(
            'ul[class*="languageList"] span[itemprop="keywords"]',
            timeout=15000
        )

        languages = page.locator(
            'ul[class*="languageList"] span[itemprop="keywords"]'
        ).all_inner_texts()

        time.sleep(1)

        if languages:
            return languages[0]

        return "不明"

    except PlaywrightTimeoutError:
        print(f"{repo_name}: 言語情報が見つかりませんでした")
        time.sleep(1)
        return "不明"

    except Exception as e:
        print(f"{repo_name}: 言語取得エラー: {e}")
        time.sleep(1)
        return "不明"


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repository_name TEXT UNIQUE,
    main_language TEXT,
    stars INTEGER
)
""")

conn.commit()


response = requests.get(
    URL,
    headers=headers,
    timeout=20
)

response.raise_for_status()

time.sleep(1)

soup = BeautifulSoup(response.text, "html.parser")

# リポジトリ名のリンクを取得
repo_links = soup.select('h3 a[href^="/google/"]')


#  Playwrightを起動する

playwright = sync_playwright().start()

browser = playwright.chromium.launch(headless=True)

page = browser.new_page()

count = 0

for repo in repo_links:

    # リポジトリ名を取得
    href = repo.get("href", "")
    repo_name = href.split("/")[-1]

    if not repo_name:
        continue

    # リポジトリカードを取得
    card = repo.parent.parent

    # スター数を取得
    star_link = card.select_one('a[href$="/stargazers"]')

    if star_link:
        star_text = (
            star_link.get("aria-label")
            or star_link.get_text(strip=True)
        )

        stars = convert_stars(star_text)

    else:
        stars = 0

    # 主要言語を取得
    language = get_main_language(page, repo_name)

    # データベースに保存
    cursor.execute("""
        INSERT INTO repositories (
            repository_name,
            main_language,
            stars
        )
        VALUES (?, ?, ?)
        ON CONFLICT(repository_name)
        DO UPDATE SET
            main_language = excluded.main_language,
            stars = excluded.stars
    """, (repo_name, language, stars))

    count += 1

    print(f"{count}. {repo_name}")
    print(f"   主要な言語: {language}")
    print(f"   スター数: {stars}")
    print("-------------------------")


browser.close()
playwright.stop()


conn.commit()

print("\nスクレイピング完了！")
print(f"{count} 件のリポジトリを取得しました。")

cursor.execute("""
SELECT repository_name, main_language, stars
FROM repositories
ORDER BY stars DESC
""")

results = cursor.fetchall()

print("\n===== データベースの内容 =====\n")

for row in results:

    print("リポジトリ名:", row[0])
    print("主要な言語:", row[1])
    print("スター数:", row[2])
    print("-------------------------")

conn.close()
