import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

SEARCH_FILE = "searches.json"
SEEN_FILE = "seen.json"

API_URL = (
    "https://api.bunjang.co.kr/api/1/find_v2.json"
    "?q={query}&order=date&page=0&n=100"
)

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]


def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_bunjang(keyword):
    encoded = urllib.parse.quote(keyword)
    url = API_URL.format(query=encoded)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://www.bunjang.com/"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def send_discord(item, keyword):
    title = item.get("name", "Unknown listing")
    price = item.get("price", "가격 정보 없음")
    pid = item.get("pid")

    url = f"https://www.bunjang.com/products/{pid}"

    message = (
        f"🚨 **NEW BUNJANG LISTING**\n\n"
        f"**Search:** `{keyword}`\n"
        f"**{title}**\n"
        f"💰 ₩{price}\n"
        f"🔗 {url}"
    )

    payload = json.dumps({
        "content": message
    }).encode("utf-8")

    request = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    urllib.request.urlopen(request, timeout=20).read()


def main():
    searches = load_json(SEARCH_FILE, {"searches": []})
    seen = load_json(SEEN_FILE, {})

    changed = False

    for keyword in searches["searches"]:

        if keyword not in seen:
            seen[keyword] = []

        data = search_bunjang(keyword)
        listings = data.get("list", [])

        for item in reversed(listings):
            pid = str(item.get("pid"))

            if not pid or pid == "None":
                continue

            if pid not in seen[keyword]:

                if len(seen[keyword]) > 0:
                    send_discord(item, keyword)

                seen[keyword].append(pid)
                changed = True

        seen[keyword] = seen[keyword][-500:]

    if changed:
        save_json(SEEN_FILE, seen)


if __name__ == "__main__":
    main()
