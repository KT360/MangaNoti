import os
import requests
from openai import OpenAI
import schedule
import time
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
SITES_FILE = "sites.json"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def load_sites():
    try:
        with open(SITES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_sites(data):
    with open(SITES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def extract_chapter(html):
    prompt = f"""
    Here is HTML from a manga website. What is the latest chapter number?
    Respond only with the number, like: 282,

    HTML:
    {html[:8000]}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return int(''.join(filter(str.isdigit, response.choices[0].message.content)))

def notify(message):
    print(f"[NOTIFY] {message}")
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        except Exception as e:
            print(f"Discord error: {e}")


def check_updates():
    sites = load_sites()
    updated = False

    for url, info in sites.items():
        title = info.get("title", "Unknown")
        last_seen = info.get("last_seen", 0)

        print(f"Checking {title} ({url})...")
        try:
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            latest = extract_chapter(text)

            if latest > last_seen:
                notify(f"📖 New chapter of **{title}**: Chapter {latest}!\n🔗 {url}")
                info["last_seen"] = latest
                updated = True
            else:
                print(f"No update for {title}. Latest is still {latest}.")
        except Exception as e:
            print(f"Error checking {url}: {e}")

    if updated:
        save_sites(sites)


schedule.every(2).days.do(check_updates)
check_updates()

while True:
    schedule.run_pending()
    time.sleep(60)
