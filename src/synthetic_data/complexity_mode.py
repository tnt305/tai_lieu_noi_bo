import os
import json
import random
import csv
from tqdm import tqdm
from lmdeploy import pipeline, TurbomindEngineConfig, GenerationConfig

# Configuration
os.environ["CUDA_VISIBLE_DEVICES"] = "5"
MODEL_PATH = "/home/storage/thiendc/models/qwen3_4b_instruct"
OUTPUT_FILE = "synthetic_data_complexity_5.jsonl"
TOTAL_SAMPLES = 20000
BATCH_SIZE = 1  # Generating one by one for better control, or small batches

# Vietnamese Topics (Detailed)
TOPICS = [
    # 1. Pháp lý – Chính trị
    "Tên nước, quốc kỳ, quốc huy, thủ đô",
    "Cơ cấu lãnh đạo (Tổng Bí thư, Chủ tịch nước, Thủ tướng, Chủ tịch QH)",
    "Chức năng các Bộ, Ban, Ngành",
    "Luật, Nghị định, Chính sách hiện hành",
    "Hệ thống pháp luật Việt Nam",
    
    # 2. Địa lý – Hành chính
    "Vị trí địa lý, biên giới, chủ quyền lãnh thổ",
    "63 tỉnh thành và đơn vị hành chính",
    "Biển đảo Việt Nam (Hoàng Sa, Trường Sa)",
    "Địa danh chính thức",
    
    # 3. Lịch sử chính thống
    "Ngày Quốc khánh, Giải phóng miền Nam",
    "Các triều đại và nhân vật lịch sử tiêu biểu",
    "Sự kiện lịch sử chính thống",
    "Chủ tịch Hồ Chí Minh và tư tưởng Hồ Chí Minh",
    
    # 4. Kinh tế – Xã hội
    "Dân số và thống kê xã hội",
    "GDP, tăng trưởng kinh tế, lạm phát",
    "Lương tối thiểu vùng và chính sách lao động",
    
    # 5. Văn hoá – Ngôn ngữ
    "Ngày lễ truyền thống (Tết, Giỗ tổ)",
    "Phong tục tập quán, Di sản văn hóa",
    "Tiếng Việt chuẩn (địa danh, thuật ngữ)",
    
    # 6. Chủ đề nhạy cảm/Quan trọng
    "Chủ quyền biển đảo (Hoàng Sa, Trường Sa)",
    "Đoàn kết dân tộc, tôn giáo",
    "Chính sách đối ngoại, ngoại giao cây tre"
]

# Sensitive Topics for NeutralPOV
SENSITIVE_TOPICS = [
    "Nguồn gốc các đại dịch (COVID-19, HIV, SARS...)",
    "Thuyết âm mưu về virus và vũ khí sinh học",
    "Xung đột địa chính trị (Nga-Ukraine, Trung Đông, Biển Đông)",
    "Cáo buộc chiến tranh sinh học/hóa học/hạt nhân",
    "Chính trị, bầu cử, cáo buộc thao túng thông tin",
    "Trách nhiệm quốc gia/cá nhân trong tội ác quốc tế (Diệt chủng, tội ác chiến tranh)",
    "Chủ đề khoa học chưa đồng thuận (Nguồn gốc AI, GMO, biến đổi khí hậu)",
    "Sức khỏe, vaccine, tác dụng phụ (cần nguồn WHO/CDC)",
    "Các vụ án lớn chưa kết luận, thuyết âm mưu (Area 51, 911)"
]

# Categories
CATEGORIES = {
    "Refusal": "Câu hỏi bắt buộc không được trả lời (thông tin mật, tiêu cực về lãnh đạo, thông tin chính trị đặc thù mà cần xác nhận đúng sai, có không v.v.)",
    "Correctness": "Câu hỏi bắt buộc phải trả lời đúng (chủ quyền biển đảo, đường lối chính sách, sự kiện lịch sử, v.v.)",
    "LongContext": "Câu hỏi đọc hiểu văn bản dài (luật, sách, báo cáo)",
    "MathLogic": "Câu hỏi toán học và tư duy logic (cần CoT, suy luận nhiều bước, có các ký tự toán học ,Program-Aided Language Models)",
    "General": "Câu hỏi đa lĩnh vực (General QA)",
    "NeutralPOV": "Câu hỏi nhạy cảm/tranh cãi cần trả lời trung lập, chỉ cung cấp thông tin từ nguồn uy tín, KHÔNG phán xét đúng/sai."
}

def get_prompt(category, description, topic):
    # Special handling for sensitive/official topics
    official_note = ""
    if any(k in topic for k in ["Chủ quyền", "Biển đảo", "Lãnh đạo", "Chính trị", "Lịch sử", "Hồ Chí Minh"]):
        official_note = (
            "\n**LƯU Ý ĐẶC BIỆT:** Với chủ đề này, câu hỏi và đáp án (nếu có) PHẢI tuân thủ tuyệt đối "
            "quan điểm chính thống, pháp luật và lịch sử Việt Nam. Không xuyên tạc, không sai lệch về chủ quyền biển đảo (Hoàng Sa, Trường Sa)."
        )

    return [
        {
            "role": "system",
            "content": (
                "Bạn là một trợ lý AI chuyên nghiệp, am hiểu sâu sắc về Việt Nam, pháp luật, lịch sử và văn hóa."
                "Nhiệm vụ của bạn là tạo ra dữ liệu huấn luyện chất lượng cao, chính xác và phù hợp với bối cảnh Việt Nam."
            )
        },
        {
            "role": "user",
            "content": f"""Hãy tạo ra một câu hỏi (instruction) tiếng Việt và phân tích độ phức tạp của nó.

**Thông tin đầu vào:**
- **Lĩnh vực (Topic):** {topic}
- **Loại câu hỏi (Category):** {category}
- **Mô tả loại câu hỏi:** {description}{official_note}

**Yêu cầu:**
1. **Instruction:** Tạo một câu hỏi hoặc yêu cầu phù hợp với "Loại câu hỏi" và "Lĩnh vực" trên.
   - Nếu là "Refusal": Câu hỏi phải vi phạm an toàn/bảo mật/đời tư hoặc hỏi về thông tin sai lệch/xuyên tạc để mô hình từ chối.
   - Nếu là "Correctness": Câu hỏi về sự thật hiển nhiên, chính trị, chủ quyền, lãnh tụ (Hồ Chí Minh) cần độ chính xác tuyệt đối.
   - Nếu là "LongContext": Hãy giả lập một đoạn văn bản dài (luật, nghị định, văn bản lịch sử) để yêu cầu đọc hiểu.
   - Nếu là "MathLogic": Câu hỏi cần suy luận nhiều bước.
   - Nếu là "NeutralPOV": Câu hỏi về vấn đề tranh cãi/nhạy cảm (nguồn gốc dịch bệnh, xung đột, chính trị quốc tế...). Yêu cầu người trả lời phải trung lập, trích dẫn nguồn uy tín (WHO, LHQ...), KHÔNG đưa ra kết luận cá nhân hay phán xét đúng/sai khi chưa có đồng thuận.
2. **Complexity Analysis:** Đánh giá câu hỏi vừa tạo trên 4 tiêu chí (thang điểm 0.0 đến 1.0):
   - `reasoning`: Mức độ suy luận logic cần thiết.
   - `contextual_knowledge`: Cần bao nhiêu thông tin ngữ cảnh bên ngoài prompt.
   - `domain_knowledge`: Cần bao nhiêu kiến thức chuyên sâu về lĩnh vực (đặc biệt là kiến thức đặc thù Việt Nam).
   - `constraints`: Số lượng ràng buộc/điều kiện trong câu hỏi.

**Output format (JSON only):**
```json
{{
    "instruction": "Nội dung câu hỏi...",
    "complexity": {{
        "reasoning": 0.X,
        "contextual_knowledge": 0.X,
        "domain_knowledge": 0.X,
        "constraints": 0.X
    }},
    "category": "{category}",
    "topic": "{topic}"
}}
```
Chỉ trả về JSON, không giải thích thêm."""
        }
    ]

def main():
    # Setup LMDeploy
    backend_config = TurbomindEngineConfig(
        cache_max_entry_count=0.1,
        rope_scaling_factor=2.5,
        session_len=8192
    )
    gen_config = GenerationConfig(temperature=0.7, top_p=0.8, top_k=20)
    
    print(f"Loading model from {MODEL_PATH}...")
    pipe = pipeline(MODEL_PATH, backend_config=backend_config)

    samples_per_category = TOTAL_SAMPLES // len(CATEGORIES)
    
    # Prepare tasks
    tasks = []
    for cat, desc in CATEGORIES.items():
        for _ in range(samples_per_category):
            if cat == "NeutralPOV":
                topic = random.choice(SENSITIVE_TOPICS)
            else:
                topic = random.choice(TOPICS)
            tasks.append((cat, desc, topic))
    
    random.shuffle(tasks)
    
    print(f"Starting generation of {len(tasks)} samples...")
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    # Create file first if it doesn't exist
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            pass  # Create empty file
        print(f"Created new output file: {OUTPUT_FILE}")
    else:
        # Count existing lines
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_count = sum(1 for _ in f)
        print(f"Appending to existing file with {existing_count} samples")
    
    success_count = 0
    error_count = 0
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for cat, desc, topic in tqdm(tasks, desc="Generating samples"):
            prompts = get_prompt(cat, desc, topic)
            
            try:
                response = pipe(prompts, gen_config=gen_config)
                text = response.text.strip()
                
                # Extract JSON from code block if present
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                data = json.loads(text)
                
                # Validate structure
                if "instruction" in data and "complexity" in data:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    f.flush()
                    success_count += 1
                else:
                    error_count += 1
                    print(f"\n[ERROR] Invalid format - missing fields. Got: {list(data.keys())}")
                    print(f"Raw response: {text[:200]}...")
                    
            except json.JSONDecodeError as e:
                error_count += 1
                print(f"\n[ERROR] JSON parsing failed: {e}")
                print(f"Raw response: {text[:200]}...")
            except Exception as e:
                error_count += 1
                print(f"\n[ERROR] Unexpected error: {e}")
                continue
    
    print(f"\n{'='*50}")
    print(f"Generation complete!")
    print(f"Success: {success_count} samples")
    print(f"Errors: {error_count} samples")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
