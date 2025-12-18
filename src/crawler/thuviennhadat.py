import json
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://thuviennhadat.vn"
SEARCH_URL = BASE_URL + "/tim-kiem-bai-viet"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

LINHVUC_LIST = range(55, 71)   # 55 → 70
PAGE_LIST = range(1, 11)       # trang 1 → 10

OUTPUT_FILE = "thuviennhadat.jsonl"


def crawl_page(linhvuc: int, page: int):
    params = {
        "trang": page,
        "linhvuc": linhvuc
    }

    response = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main_content = soup.find("div", class_="ui divided items")

    if not main_content:
        return []

    results = []

    for item in main_content.find_all("div", class_="item"):
        try:
            a_tag = item.find("a", class_="header")
            if not a_tag:
                continue

            url = BASE_URL + a_tag.get("href")
            content = a_tag.get_text(strip=True)

            results.append({
                "content": content,
                "url": url,
                "linhvuc": linhvuc,
                "page": page
            })

        except Exception as e:
            print(f"Lỗi parse item: {e}")

    return results


with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
    for linhvuc in LINHVUC_LIST:
        for page in PAGE_LIST:
            print(f"Đang crawl: linhvuc={linhvuc}, trang={page}")

            try:
                items = crawl_page(linhvuc, page)
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            except Exception as e:
                print(f"Lỗi khi crawl linhvuc={linhvuc}, trang={page}: {e}")


