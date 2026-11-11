
from playwright.sync_api import sync_playwright

url = "https://github.com/google/adk-python"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # GitHubのページを開く
    page.goto(url, wait_until="domcontentloaded")

    # JavaScriptによる表示を待つ
    page.wait_for_timeout(5000)

    # Languagesという見出しを探す
    # Languagesの見出しを探す
    heading = page.get_by_role("heading", name="Languages")

    print("Languagesの見出し:", heading.count())

    # 2つ目の見出しがサイドバーにある
    if heading.count() >= 2:

        section = heading.nth(1).locator("xpath=..")

        print("\n===== LanguagesのHTML =====")
        print(section.evaluate("(element) => element.outerHTML"))

        print("\n===== Languagesの表示内容 =====")
        print(section.inner_text())

        # 言語名と割合を取得
        print("\n===== 言語情報 =====")

        print(section.locator("a").all_inner_texts())

        browser.close()

    if heading.count() > 0:
        # 見出しの親要素を取得
        section = heading.locator("xpath=..")

        print("\n===== LanguagesのHTML =====")
        print(section.evaluate("(element) => element.outerHTML"))

        print("\n===== Languagesの表示内容 =====")
        print(section.inner_text())

    browser.close()
