import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from src.crawler.domain_cfg import THUVIENPHAPLUAT_CFG_MAPPING

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

main_url = "https://thuvienphapluat.vn"
output_path = "src/crawler/fullthuvienphapluat.jsonl"

with open(output_path, "a", encoding="utf-8") as f:
    for domain_name, domain_url in THUVIENPHAPLUAT_CFG_MAPPING.items():
        for page in tqdm(range(0, 50), desc=domain_name):
            try:
                url = f"{domain_url}?page={page}"
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                articles = soup.find_all("article", class_="news-card")
                if not articles:
                    continue

                for item in articles:
                    a_tag = item.find("a")
                    if not a_tag:
                        continue

                    item_url = main_url + a_tag.get("href")
                    content = a_tag.get("title", "").strip()

                    f.write(
                        json.dumps(
                            {"url": item_url, "content": content},
                            ensure_ascii=False
                        ) + "\n"
                    )

            except Exception as e:
                print(f"[ERROR] {domain_name} page {page}: {e}")
