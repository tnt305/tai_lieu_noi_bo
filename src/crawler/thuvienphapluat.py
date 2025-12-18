import os
import json
from tqdm import tqdm
from src import load_tvpl_url, crawl_with_selenium


def append_jsonl_dedup(filepath: str, item: dict, dedup_key="url"):
    """
    Append vào jsonl file, nhưng kiểm tra trùng theo key trước khi ghi.
    """
    # Nếu file chưa tồn tại → tạo rỗng
    if not os.path.exists(filepath):
        open(filepath, "w").close()

    # Đọc từng dòng để check trùng (streaming – không load hết file)
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get(dedup_key) == item.get(dedup_key):
                    return False  # Bỏ qua vì đã trùng
            except:
                continue

    # Nếu không trùng → append
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return True


BASE_URL, urls = load_tvpl_url(mode="full")

list_urls=[]
for url in tqdm(urls):
    soup = crawl_with_selenium(url, wait_time=5)
    try:
        if soup.find("div", class_="cmPager").find_all("a") == []:
            list_urls.append(url)
        else:
            urls_with_page=list(dict.fromkeys([f"{BASE_URL}/{a['href']}" for a in soup.find("div", class_="cmPager").find_all("a")]))
            list_urls.extend(urls_with_page)
    except:
        print("No pagination for url: ", url)
        continue

output_path = "nghidinh.jsonl"  
for url in tqdm(list_urls):
    soup = crawl_with_selenium(url, wait_time=5)
    nghidinh_urls = soup.find("div", id="ctl00_Content_VanBanMoi_divKetQuaVB").find_all("a", onclick="Doc_CT(MemberGA)")
    if nghidinh_urls is None or len(nghidinh_urls) == 0:
        raise ValueError("No nghidinh found")
        pass
    for nghidinh in tqdm(nghidinh_urls):
        url = nghidinh.get("href")
        content = nghidinh.get_text(strip=True)
        prefetch_item = {
            "content": content,
            "url": url,
        }

        append_jsonl_dedup(output_path, prefetch_item)