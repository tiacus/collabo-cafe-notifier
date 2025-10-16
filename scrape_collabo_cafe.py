import requests
from bs4 import BeautifulSoup
import os
import json
import sys

# --- 定数設定 ---
URL = "https://collabo-cafe.com/"
KEYWORDS = ["原神", "ゼンゼロ", "ゼンレスゾーンゼロ", "ちいかわ","カービィ"]
NOTIFIED_URLS_FILE = "notified_urls.txt"

# --- LINE Messaging API 設定 ---
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('LINE_USER_ID')
LINE_API_URL = 'https://api.line.me/v2/bot/message/push'

def load_notified_urls():
    """通知済みのURLをファイルから読み込む"""
    if not os.path.exists(NOTIFIED_URLS_FILE):
        return set()
    with open(NOTIFIED_URLS_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def save_new_urls(urls):
    """新しく通知したURLをファイルに追記する"""
    with open(NOTIFIED_URLS_FILE, 'a', encoding='utf-8') as f:
        for url in urls:
            f.write(url + '\n')

def send_line_notification(articles):
    """見つかった記事の情報をLINEで通知する"""
    if not articles:
        return
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    message_text = f"新しいコラボ情報が{len(articles)}件見つかりました！\n\n"
    for article in articles:
        message_text += f"■ {article['title']}\n{article['url']}\n\n"
    payload = {
        'to': USER_ID,
        'messages': [{'type': 'text', 'text': message_text.strip()}]
    }
    try:
        response = requests.post(LINE_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"{len(articles)}件のLINE通知を送信しました。")
    except requests.exceptions.RequestException as e:
        print(f"LINE通知の送信に失敗しました: {e}")
        if e.response:
            print(f"Response: {e.response.text}")

def scrape_and_notify():
    """ウェブサイトをスクレイピングして新しい記事があればLINEで通知する"""
    # 実行前チェック
    if not CHANNEL_ACCESS_TOKEN or not USER_ID:
        print("エラー: 環境変数 'LINE_CHANNEL_ACCESS_TOKEN' または 'LINE_USER_ID' が設定されていません。")
        sys.exit(1)

    try:
        processed_urls = load_notified_urls()
        print(f"読み込み完了: {len(processed_urls)}件の通知済みURLがあります。")

        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        articles = soup.find_all("article", class_="post-list")
        if not articles:
            print("記事が見つかりませんでした。サイトの構造が変更された可能性があります。")
            return

        articles_for_notification = []
        newly_notified_urls = []

        for article in articles:
            link_tag = article.find("a")
            if not link_tag or not link_tag.has_attr('href'):
                continue
            url = link_tag["href"]

            if url in processed_urls:
                continue

            title_tag = article.find("h1", class_="entry-title")
            title = title_tag.text.strip() if title_tag else "No Title"

            if any(keyword in title for keyword in KEYWORDS):
                articles_for_notification.append({'title': title, 'url': url})
                newly_notified_urls.append(url)

        if articles_for_notification:
            send_line_notification(articles_for_notification)
            save_new_urls(newly_notified_urls)
            print(f"保存完了: {len(newly_notified_urls)}件の新しいURLを{NOTIFIED_URLS_FILE}に追記しました。")
        else:
            print("キーワードに一致する新しい記事はありませんでした。")

    except requests.exceptions.RequestException as e:
        print(f"サイトへのアクセスに失敗しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*50)
    print("コラボカフェ情報のチェックを開始します...")
    scrape_and_notify()
    print("チェックが完了しました。")
    print("="*50 + "\n")
