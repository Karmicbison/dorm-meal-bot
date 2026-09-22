import datetime
import os
import re
from bs4 import BeautifulSoup
import requests

# GitHub 비밀 설정(Secrets)에서 웹훅 URL을 가져옵니다.
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
URL = "https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20041&type=2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def clean_menu_text(text):
    """원산지/칼로리 제거 후 각 메뉴 항목을 줄바꿈(\\n)으로 구분하여 정렬하는 함수"""
    text = re.sub(r"\([^)]*산[^)]*\)", "", text)
    text = re.sub(r"\d+kcal/\d+g", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "식단 정보가 없습니다."

    items = text.split(" ")
    formatted_items = []

    for item in items:
        item = item.strip()
        if item:
            formatted_items.append(f"• {item}")

    return "\n".join(formatted_items)


def fetch_today_menu():
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    response = requests.get(URL, headers=HEADERS)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")

    for row in rows:
        row_text = row.get_text()
        if today_str in row_text:
            cols = row.find_all(["td", "th"])
            if len(cols) >= 4:
                breakfast = clean_menu_text(cols[1].get_text(separator=" "))
                lunch = clean_menu_text(cols[2].get_text(separator=" "))
                dinner = clean_menu_text(cols[3].get_text(separator=" "))

                return {
                    "date": today_str,
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "dinner": dinner,
                }

    return None


def send_to_discord(menu_data):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL 환경 변수가 설정되지 않았습니다.")
        return

    if not menu_data:
        payload = {
            "embeds": [
                {
                    "title": "🍱 충북대 양성재 오늘의 식단",
                    "description": "오늘 날짜의 식단 정보를 찾을 수 없습니다 (휴무일 또는 미등록).",
                    "color": 15158332,
                }
            ]
        }
    else:
        payload = {
            "embeds": [
                {
                    "title": f"🍱 충북대 양성재 식단 ({menu_data['date']})",
                    "color": 3447003,
                    "fields": [
                        {
                            "name": "🌅 아침",
                            "value": menu_data["breakfast"],
                            "inline": False,
                        },
                        {
                            "name": "☀️ 점심",
                            "value": menu_data["lunch"],
                            "inline": False,
                        },
                        {
                            "name": "🌙 저녁",
                            "value": menu_data["dinner"],
                            "inline": False,
                        },
                    ],
                    "footer": {
                        "text": "충북대학교 생활관 홈페이지 기준 (양성재)"
                    },
                }
            ]
        }

    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code in (200, 204):
        print("✅ 디스코드 전송 성공!")
    else:
        print(f"❌ 디스코드 전송 실패 (상태 코드: {res.status_code})")


if __name__ == "__main__":
    menu = fetch_today_menu()
    send_to_discord(menu)