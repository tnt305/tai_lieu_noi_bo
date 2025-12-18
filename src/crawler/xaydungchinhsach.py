import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm

base_url = "https://xaydungchinhsach.chinhphu.vn/chinh-sach-moi.htm"
headers = {"User-Agent": "Mozilla/5.0"}

MAX_PAGE = 50

with open("./src/crawler/xaydungchinhsach.jsonl", "a", encoding="utf-8") as f:
    for page in tqdm(range(1, MAX_PAGE + 1), desc="Crawling pages"):
        url = f"{base_url}?page={page}"
        resp = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("div", class_="box-category-item")

        # dừng sớm nếu không còn dữ liệu
        if not items:
            tqdm.write(f"Stop at page {page} (no items)")
            break

        for item in items:
            a = item.find("a", href=True)

            data = {
                "content": a.get("title", "").strip(),
                "url": "https://xaydungchinhsach.chinhphu.vn" + a["href"]
            }

            f.write(json.dumps(data, ensure_ascii=False) + "\n")
