import json
import re
import trafilatura
from urllib.parse import urljoin
from tqdm import tqdm

import requests
from bs4 import BeautifulSoup

import sys
import os
sys.path.append(os.getcwd())

from src.crawler.domain_cfg import WIKI_CFG_MAPPING

url = WIKI_CFG_MAPPING["HCM"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

html = requests.get(url, headers=headers).text

soup = BeautifulSoup(html, "html.parser")

# Deduplication set
seen_urls = set()
# Clear file before writing
if os.path.exists("src/crawler/hcm.jsonl"):
    os.remove("src/crawler/hcm.jsonl")

external_references = soup.find("div", class_="reflist").find_all("span", class_="reference-text")
for item in external_references:
    try:
        url = item.find("cite").find("a", class_="external").get("href")
        content = item.find("cite").find("a", class_="external").text.strip('"')
        
        if url in seen_urls:
            continue
            
        jsonl_data= {"content": content, "url": url}
        seen_urls.add(url)
        
        with open("src/crawler/hcm.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(jsonl_data, ensure_ascii=False) + "\n")
    except:
        pass

# Fix: find_all("a") to get all links within the content div
content_div = soup.find("div", class_="mw-content-ltr")
if content_div:
    internal_references = content_div.find_all("a")
    for item in internal_references:
        try:
            content = item.get("title")
            href = item.get("href")
            if not href or not href.startswith("/wiki/"):
                continue
                
            url = "https://vi.wikipedia.org" + href
            
            if url in seen_urls:
                continue

            if content is None or content=="None" or url.endswith("svg") or content.startswith("Thể loại:"):
                continue

            jsonl_data= {"content": content, "url": url}
            seen_urls.add(url)

            with open("src/crawler/hcm.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(jsonl_data, ensure_ascii=False) + "\n")
        except:
            pass
