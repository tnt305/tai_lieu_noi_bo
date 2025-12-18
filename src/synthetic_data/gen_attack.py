import csv
import json
from tqdm import tqdm
import os
from lmdeploy import pipeline, TurbomindEngineConfig
os.environ["CUDA_VISIBLE_DEVICES"] = "5"

backend_config = TurbomindEngineConfig(cache_max_entry_count=0.2)

output_path = "translated_output.jsonl"

with pipeline(
    "/home/storage/thiendc/models/qwen3_4b_instruct",
    backend_config=backend_config
) as pipe, open("./src/synthetic_data/train.csv", "r", newline="", encoding="utf-8") as f, open(output_path, "a", encoding="utf-8") as out_f:

    reader = csv.reader(f)
    header = next(reader)

    # Đếm số dòng để tqdm biết tổng số
    rows = list(reader)

    for row in tqdm(rows, desc="Processing"):
        prompts = [
            {
                "role": "system",
                "content": (
                    "Bạn là một chuyên gia dịch thuật và biên tập viên nội dung sang tiếng Việt. "
                    "Nhiệm vụ của bạn là dịch đoạn văn dưới đây sang tiếng Việt một cách tự nhiên và trôi chảy.\n\n"
                    "NGUYÊN TẮC CỐT LÕI:\n"
                    "1. Tự nhiên hơn chính xác.\n"
                    "2. Không dùng Hán tự.\n"
                    "3. Chỉ xuất văn bản tiếng Việt, không giải thích.\n"
                    "4. Nếu có từ hai câu hỏi trở lên, hãy rewrite đoạn văn để còn duy nhất 1 câu hỏi."
                )
            },
            {
                "role": "user",
                "content": f"Dịch đoạn văn sau sang tiếng Việt:\n\n{row[0]}"
            }
        ]

        response = pipe(prompts)
        record = {"text": response.text.strip(), "label": row[1]}

        # Ghi ngay vào JSONL để tránh mất dữ liệu
        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
        out_f.flush()
        del record, response

print("Done training set, start testing set")

output_path = "translated_output_test.jsonl"
with pipeline(
    "/home/storage/thiendc/models/qwen3_4b_instruct",
    backend_config=backend_config
) as pipe, open("./src/synthetic_data/test.csv", "r", newline="", encoding="utf-8") as f, open(output_path, "a", encoding="utf-8") as out_f:

    reader = csv.reader(f)
    header = next(reader)

    # Đếm số dòng để tqdm biết tổng số
    rows = list(reader)

    for row in tqdm(rows, desc="Processing"):
        prompts = [
            {
                "role": "system",
                "content": (
                    "Bạn là một chuyên gia dịch thuật và biên tập viên nội dung sang tiếng Việt. "
                    "Nhiệm vụ của bạn là dịch đoạn văn dưới đây sang tiếng Việt một cách tự nhiên và trôi chảy.\n\n"
                    "NGUYÊN TẮC CỐT LÕI:\n"
                    "1. Tự nhiên hơn chính xác.\n"
                    "2. Không dùng Hán tự.\n"
                    "3. Chỉ xuất văn bản tiếng Việt, không giải thích.\n"
                    "4. Nếu có từ hai câu hỏi trở lên, hãy rewrite đoạn văn để còn duy nhất 1 câu hỏi."
                )
            },
            {
                "role": "user",
                "content": f"Dịch đoạn văn sau sang tiếng Việt:\n\n{row[0]}"
            }
        ]

        response = pipe(prompts)
        record = {"text": response.text.strip(), "label": row[1]}

        # Ghi ngay vào JSONL để tránh mất dữ liệu
        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
        out_f.flush()
        del record, response