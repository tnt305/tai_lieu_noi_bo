import json
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

start_url = "https://vi.wikipedia.org/wiki/Th%E1%BB%83_lo%E1%BA%A1i:Danh_s%C3%A1ch_nh%C3%A2n_v%E1%BA%ADt_Vi%E1%BB%87t_Nam"
output_path = "src/crawler/wiki_chinhtri.jsonl"

visited = set()  # 👉 dedup toàn bộ URL

def normalize_wiki_url(href: str):
    if not href.startswith("/wiki/"):
        return None
    if any(href.startswith(x) for x in ["/wiki/Wikipedia:", "/wiki/Help:", "/wiki/Special:"]):
        return None
    return "https://vi.wikipedia.org" + href


with open(output_path, "a", encoding="utf-8", buffering=1) as f:
    response = requests.get(start_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    for item in soup.select("#mw-pages a"):
        title = item.get("title")
        href = item.get("href")

        if not title or ":" in title:
            continue

        url = normalize_wiki_url(href)
        if not url or url in visited:
            continue

        visited.add(url)
        f.write(json.dumps({"content": title.strip(), "url": url}, ensure_ascii=False) + "\n")

        # crawl trang chi tiết
        r = requests.get(url, headers=headers)
        s = BeautifulSoup(r.text, "html.parser")

        for a in s.select("div.mw-body-content a[href^='/wiki/']"):
            sub_url = normalize_wiki_url(a.get("href"))
            sub_title = a.get("title")

            if not sub_url or not sub_title:
                continue
            if sub_url in visited:
                continue

            visited.add(sub_url)
            f.write(
                json.dumps(
                    {"content": sub_title.strip(), "url": sub_url},
                    ensure_ascii=False
                ) + "\n"
            )
