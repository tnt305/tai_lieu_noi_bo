import json
from src.crawler.domain_cfg import THONG_TIN_CHINH_PHU_CFG_MAPPING
output_file = "./thong_tin_chinh_phu.jsonl"

with open(output_file, "w", encoding="utf-8") as f:
    for content, url in THONG_TIN_CHINH_PHU_CFG_MAPPING.items():
        line = {
            "content": content,
            "url": url
        }
        f.write(json.dumps(line, ensure_ascii=False) + "\n")