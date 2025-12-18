import os
import json
import random
from tqdm import tqdm
from lmdeploy import pipeline, TurbomindEngineConfig, GenerationConfig

# Configuration
os.environ["CUDA_VISIBLE_DEVICES"] = "5"
MODEL_PATH = "/home/storage/thiendc/models/qwen3_4b_instruct"
INPUT_FILE = "/home/thiendc/projects/hitman/synthetic_data_complexity_done.jsonl"
OUTPUT_FILE = "synthetic_data_complexity_2025.jsonl"
TOTAL_SAMPLES = 5000  # Number of new samples to generate

# Topics/Events in Vietnam 2025
VIETNAM_2025_TOPICS = [
    # Sự kiện chính trị - xã hội 2025
    "Đại hội Đảng Cộng sản Việt Nam lần thứ XIV (dự kiến 2026, chuẩn bị 2025)",
    "Kỷ niệm 50 năm ngày giải phóng miền Nam, thống nhất đất nước (30/4/2025)",
    "Kỷ niệm 80 năm ngày Cách mạng tháng Tám và Quốc khánh (2/9/2025)",
    "Kỷ niệm 135 năm ngày sinh Chủ tịch Hồ Chí Minh (19/5/2025)",
    
    # Kinh tế 2025
    "Mục tiêu tăng trưởng GDP Việt Nam năm 2025 (6.5-7%)",
    "Chính sách tiền lương mới và cải cách tiền lương năm 2025",
    "Đầu tư công và các dự án hạ tầng trọng điểm 2025",
    "Phát triển kinh tế số và chuyển đổi số quốc gia 2025",
    "FDI và thu hút đầu tư nước ngoài năm 2025",
    
    # Hạ tầng giao thông 2025
    "Tiến độ đường sắt cao tốc Bắc-Nam",
    "Các tuyến metro tại TP.HCM và Hà Nội năm 2025",
    "Sân bay Long Thành - tiến độ xây dựng 2025",
    "Cao tốc Bắc-Nam phía Đông hoàn thành các đoạn 2025",
    
    # Giáo dục 2025
    "Chương trình giáo dục phổ thông mới 2018 - thực hiện đầy đủ 2025",
    "Kỳ thi tốt nghiệp THPT và tuyển sinh đại học 2025",
    "Chính sách học phí và hỗ trợ sinh viên 2025",
    
    # Y tế - Môi trường 2025
    "Chính sách bảo hiểm y tế và chăm sóc sức khỏe 2025",
    "Biến đổi khí hậu và ứng phó thiên tai tại Việt Nam 2025",
    "Ô nhiễm môi trường và các giải pháp xử lý 2025",
    
    # Công nghệ - AI 2025
    "Chiến lược phát triển AI quốc gia Việt Nam đến 2030",
    "Ứng dụng AI trong quản lý nhà nước và dịch vụ công 2025",
    "Startup và hệ sinh thái khởi nghiệp Việt Nam 2025",
    "An ninh mạng và bảo vệ dữ liệu cá nhân 2025",
    
    # Quan hệ quốc tế 2025
    "Quan hệ Việt Nam - Mỹ: Đối tác chiến lược toàn diện 2025",
    "Quan hệ Việt Nam - Trung Quốc năm 2025",
    "Việt Nam và ASEAN năm 2025",
    "Hợp tác Việt Nam - Nhật Bản, Hàn Quốc 2025",
    
    # Thể thao - Văn hóa 2025
    "SEA Games và các giải đấu thể thao Việt Nam tham gia 2025",
    "Di sản văn hóa UNESCO của Việt Nam",
    "Festival và sự kiện văn hóa lớn năm 2025",
    
    # An ninh - Quốc phòng 2025
    "Bảo vệ chủ quyền biển đảo và an ninh Biển Đông 2025",
    "Hiện đại hóa quốc phòng và an ninh quốc gia",
]

# Math/Logic topics with LaTeX notation and real-world Vietnam 2025 applications
MATH_LOGIC_TOPICS = [
    # Lượng giác - Trigonometry
    {
        "topic": "Bài toán lượng giác trong kỹ thuật xây dựng",
        "example": "Cho $ \\theta $ là góc nghiêng của một cây cầu dây văng. Biết $ \\tan \\theta + \\cot \\theta = 4 $, tính $ \\sin 2\\theta $ để xác định lực căng dây.",
        "context": "Xây dựng cầu Mỹ Thuận 2, cầu Cần Giờ năm 2025"
    },
    {
        "topic": "Lượng giác trong đo đạc địa chính",
        "example": "Một máy đo góc đặt tại điểm $ A $ đo được góc $ \\alpha $ đến đỉnh tòa nhà. Biết $ \\cos^2 \\alpha - \\sin^2 \\alpha = \\frac{1}{2} $, tìm $ \\tan \\alpha $.",
        "context": "Quy hoạch đô thị TP.HCM và Hà Nội 2025"
    },
    {
        "topic": "Hàm số lượng giác trong dao động",
        "example": "Biên độ dao động của tuyến metro được mô tả bởi $ y = A\\sin(\\omega t + \\varphi) $. Cho $ \\sin \\varphi + \\cos \\varphi = \\frac{\\sqrt{6}}{2} $, tìm $ \\sin 2\\varphi $.",
        "context": "Vận hành metro Bến Thành - Suối Tiên năm 2025"
    },
    
    # Giải tích - Calculus
    {
        "topic": "Đạo hàm và tối ưu hóa chi phí",
        "example": "Chi phí sản xuất $ C(x) = x^3 - 6x^2 + 15x + 10 $ (triệu đồng). Tìm $ x $ để $ C'(x) = 0 $ và xác định điểm cực trị.",
        "context": "Tối ưu hóa sản xuất công nghiệp Việt Nam 2025"
    },
    {
        "topic": "Tích phân trong tính toán diện tích",
        "example": "Diện tích đất thu hồi được giới hạn bởi $ y = x^2 $ và $ y = 2x $. Tính $ \\int_0^2 (2x - x^2) dx $ để xác định diện tích.",
        "context": "Giải phóng mặt bằng sân bay Long Thành 2025"
    },
    {
        "topic": "Phương trình vi phân trong dịch tễ học",
        "example": "Số ca nhiễm $ I(t) $ thỏa mãn $ \\frac{dI}{dt} = rI(1 - \\frac{I}{K}) $. Cho $ r = 0.3 $, $ K = 10000 $, tìm $ I $ khi $ \\frac{dI}{dt} = 0 $.",
        "context": "Dự báo dịch bệnh và y tế công cộng Việt Nam 2025"
    },
    
    # Đại số - Algebra
    {
        "topic": "Hệ phương trình trong phân bổ ngân sách",
        "example": "Ngân sách đầu tư công: $ x + y + z = 700 $ (nghìn tỷ), $ 2x - y = 100 $, $ y + 2z = 400 $. Giải hệ để tìm phân bổ cho từng lĩnh vực.",
        "context": "Kế hoạch đầu tư công trung hạn 2025-2030"
    },
    {
        "topic": "Ma trận trong phân tích dữ liệu",
        "example": "Ma trận chuyển đổi $ A = \\begin{pmatrix} 2 & 1 \\\\ 1 & 3 \\end{pmatrix} $. Tính $ \\det(A) $ và $ A^{-1} $ để giải bài toán tối ưu.",
        "context": "Chuyển đổi số và phân tích dữ liệu quốc gia 2025"
    },
    {
        "topic": "Phương trình bậc hai trong kinh tế",
        "example": "Doanh thu $ R(p) = -2p^2 + 100p $ (triệu đồng) với $ p $ là giá bán. Tìm $ p $ để $ R(p) $ đạt cực đại.",
        "context": "Chiến lược giá cả và thương mại điện tử Việt Nam 2025"
    },
    
    # Xác suất - Thống kê
    {
        "topic": "Xác suất có điều kiện trong dự báo",
        "example": "$ P(A) = 0.6 $, $ P(B|A) = 0.8 $, $ P(B|\\bar{A}) = 0.3 $. Tính $ P(A|B) $ theo công thức Bayes.",
        "context": "Dự báo kinh tế và thị trường chứng khoán Việt Nam 2025"
    },
    {
        "topic": "Phân phối chuẩn trong thống kê dân số",
        "example": "Thu nhập $ X \\sim N(\\mu, \\sigma^2) $ với $ \\mu = 8 $ triệu, $ \\sigma = 2 $ triệu. Tính $ P(6 < X < 10) $ dùng bảng phân phối chuẩn.",
        "context": "Thống kê thu nhập và an sinh xã hội Việt Nam 2025"
    },
    {
        "topic": "Hồi quy tuyến tính trong phân tích",
        "example": "Cho dữ liệu GDP và FDI, tìm đường hồi quy $ \\hat{y} = ax + b $ với $ a = \\frac{\\sum(x_i - \\bar{x})(y_i - \\bar{y})}{\\sum(x_i - \\bar{x})^2} $.",
        "context": "Phân tích mối quan hệ FDI và tăng trưởng GDP 2025"
    },
    
    # Hình học - Geometry
    {
        "topic": "Hình học không gian trong kiến trúc",
        "example": "Một tòa nhà hình trụ có bán kính $ r $ và chiều cao $ h $. Thể tích $ V = \\pi r^2 h = 1000 $ m³. Tìm $ r $ để diện tích xung quanh $ S = 2\\pi rh $ nhỏ nhất.",
        "context": "Thiết kế kiến trúc xanh và tiết kiệm vật liệu 2025"
    },
    {
        "topic": "Vector trong định vị GPS",
        "example": "Cho $ \\vec{a} = (3, 4) $ và $ \\vec{b} = (1, 2) $. Tính $ \\vec{a} \\cdot \\vec{b} $, $ |\\vec{a}| $, và góc giữa hai vector.",
        "context": "Hệ thống định vị và giao thông thông minh Việt Nam 2025"
    },
    
    # Toán tài chính
    {
        "topic": "Lãi suất kép và đầu tư",
        "example": "Số tiền $ A = P(1 + \\frac{r}{n})^{nt} $ với $ P = 100 $ triệu, $ r = 7\\% $, $ n = 12 $, $ t = 5 $. Tính $ A $ và lãi suất thực $ (1 + \\frac{r}{n})^n - 1 $.",
        "context": "Lãi suất ngân hàng và đầu tư tài chính Việt Nam 2025"
    },
    {
        "topic": "Quy hoạch tuyến tính trong logistics",
        "example": "Tối đa hóa $ Z = 3x + 5y $ với ràng buộc $ x + 2y \\leq 100 $, $ 2x + y \\leq 80 $, $ x, y \\geq 0 $. Tìm $ (x, y) $ tối ưu.",
        "context": "Tối ưu hóa vận chuyển và logistics Việt Nam 2025"
    },
    {
        "topic": "Chuỗi thời gian trong dự báo",
        "example": "Dự báo GDP: $ y_t = \\alpha y_{t-1} + (1-\\alpha)\\hat{y}_{t-1} $ với $ \\alpha = 0.3 $. Cho $ y_0 = 400 $, $ \\hat{y}_0 = 380 $, tính $ \\hat{y}_1, \\hat{y}_2 $.",
        "context": "Dự báo kinh tế vĩ mô Việt Nam 2025"
    },
    
    # Logic và Thuật toán
    {
        "topic": "Logic mệnh đề trong luật pháp",
        "example": "Cho $ p $: 'Công dân đủ 18 tuổi', $ q $: 'Có quyền bầu cử'. Biểu diễn và kiểm tra tính đúng/sai của $ p \\Rightarrow q $, $ \\neg p \\lor q $.",
        "context": "Bầu cử Quốc hội và logic pháp luật Việt Nam 2025"
    },
    {
        "topic": "Thuật toán và độ phức tạp",
        "example": "Thuật toán sắp xếp có độ phức tạp $ O(n \\log n) $. Với $ n = 10^6 $, ước tính số phép tính và so sánh với $ O(n^2) $.",
        "context": "Phát triển phần mềm và công nghệ AI Việt Nam 2025"
    },
    {
        "topic": "Lý thuyết đồ thị trong giao thông",
        "example": "Đồ thị có $ V $ đỉnh và $ E $ cạnh. Tìm đường đi ngắn nhất từ $ A $ đến $ B $ với thuật toán Dijkstra. Cho ma trận trọng số $ W $.",
        "context": "Tối ưu hóa giao thông đô thị Việt Nam 2025"
    },
    
    # Số học và Tổ hợp
    {
        "topic": "Tổ hợp trong bầu cử",
        "example": "Có $ n = 500 $ đại biểu, chọn $ k = 50 $ vào Ủy ban. Số cách chọn $ C_n^k = \\frac{n!}{k!(n-k)!} $. Tính và ước lượng.",
        "context": "Bầu cử Quốc hội khóa XVI năm 2026, chuẩn bị 2025"
    },
    {
        "topic": "Dãy số trong tăng trưởng",
        "example": "GDP tăng theo cấp số nhân $ u_n = u_1 \\cdot q^{n-1} $ với $ u_1 = 400 $ tỷ USD, $ q = 1.065 $. Tính $ u_5 $ và $ S_5 = \\frac{u_1(q^5 - 1)}{q - 1} $.",
        "context": "Dự báo GDP Việt Nam giai đoạn 2025-2030"
    },
]


def normalize_instruction(instruction: str) -> str:
    """Normalize instruction for deduplication comparison."""
    normalized = instruction.lower().strip()
    normalized = ' '.join(normalized.split())
    return normalized


def load_existing_instructions(filepath: str) -> set:
    """Load existing instructions from output file for deduplication."""
    existing_instructions = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if "instruction" in data:
                        normalized = normalize_instruction(data["instruction"])
                        existing_instructions.add(normalized)
                except json.JSONDecodeError:
                    continue
    return existing_instructions


def load_source_samples(filepath: str) -> list:
    """Load source samples from input file."""
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if "instruction" in data and "complexity" in data:
                    samples.append(data)
            except json.JSONDecodeError:
                continue
    return samples


def get_transform_prompt(original_sample: dict, topic_info: dict | str):
    """Generate prompt to transform original sample to 2025 Vietnam context."""
    
    original_instruction = original_sample.get("instruction", "")
    original_category = original_sample.get("category", "General")
    original_topic = original_sample.get("topic", "")
    original_complexity = original_sample.get("complexity", {})
    
    # Handle MathLogic category with special math topics
    if original_category == "MathLogic" and isinstance(topic_info, dict):
        math_topic = topic_info.get("topic", "")
        math_example = topic_info.get("example", "")
        math_context = topic_info.get("context", "")
        
        return [
            {
                "role": "system",
                "content": (
                    "Bạn là một trợ lý AI chuyên nghiệp về toán học và logic, am hiểu sâu sắc về các bài toán ứng dụng thực tế. "
                    "Nhiệm vụ của bạn là tạo ra câu hỏi toán học chất lượng cao với ký hiệu LaTeX chuẩn, áp dụng vào bối cảnh Việt Nam năm 2025."
                )
            },
            {
                "role": "user",
                "content": f"""Hãy tạo một bài toán/câu hỏi logic MỚI HOÀN TOÀN với ngữ cảnh thực tế tại Việt Nam năm 2025.

**Tham khảo dạng bài (KHÔNG copy):**
- Topic: {math_topic}
- Ví dụ format: {math_example}
- Ngữ cảnh áp dụng: {math_context}

**Câu hỏi mẫu gốc (tham khảo cấu trúc):**
- Instruction: {original_instruction}

**Yêu cầu QUAN TRỌNG:**
1. Tạo bài toán MỚI HOÀN TOÀN - khác nội dung và số liệu so với ví dụ
2. SỬ DỤNG KÝ HIỆU LATEX: dùng $ ... $ cho công thức inline
   - Ví dụ: $ \\sin \\theta $, $ \\frac{{a}}{{b}} $, $ \\sqrt{{x}} $, $ \\int_0^1 f(x) dx $
   - Greek letters: $ \\alpha $, $ \\beta $, $ \\theta $, $ \\pi $
   - Operations: $ \\times $, $ \\div $, $ \\pm $, $ \\leq $, $ \\geq $
   - Functions: $ \\log $, $ \\ln $, $ \\exp $, $ \\lim $
3. Bài toán phải có BỐI CẢNH THỰC TẾ Việt Nam 2025 (kinh tế, xây dựng, giao thông, y tế, giáo dục...)
4. Yêu cầu giải quyết NHIỀU BƯỚC (CoT - Chain of Thought)
5. Có thể yêu cầu viết code Python để giải (Program-Aided)

**Các dạng bài:**
- Lượng giác: $ \\sin $, $ \\cos $, $ \\tan $, $ \\cot $, hàm số lượng giác
- Giải tích: đạo hàm $ f'(x) $, tích phân $ \\int $, giới hạn $ \\lim $
- Đại số: hệ phương trình, ma trận, vector
- Xác suất thống kê: $ P(A|B) $, phân phối $ N(\\mu, \\sigma^2) $
- Tài chính: lãi suất kép, NPV, IRR
- Tối ưu hóa: quy hoạch tuyến tính, cực trị

**Output format (JSON only):**
```json
{{
    "instruction": "Bài toán với ký hiệu LaTeX $ ... $ và bối cảnh Việt Nam 2025...",
    "complexity": {{
        "reasoning": 0.X,
        "contextual_knowledge": 0.X,
        "domain_knowledge": 0.X,
        "constraints": 0.X
    }},
    "category": "MathLogic",
    "topic": "{math_topic}"
}}
```
Chỉ trả về JSON, không giải thích thêm."""
            }
        ]
    
    # Default prompt for other categories
    vietnam_2025_topic = topic_info if isinstance(topic_info, str) else topic_info.get("topic", "")
    
    return [
        {
            "role": "system",
            "content": (
                "Bạn là một trợ lý AI chuyên nghiệp, am hiểu sâu sắc về Việt Nam, pháp luật, lịch sử, kinh tế và các sự kiện thời sự. "
                "Nhiệm vụ của bạn là tạo ra dữ liệu huấn luyện chất lượng cao, chính xác và phù hợp với bối cảnh Việt Nam năm 2025."
            )
        },
        {
            "role": "user",
            "content": f"""Dựa trên câu hỏi mẫu bên dưới, hãy tạo ra một câu hỏi MỚI HOÀN TOÀN KHÁC về nội dung nhưng liên quan đến ngữ cảnh Việt Nam năm 2025.

**Câu hỏi mẫu gốc:**
- Instruction: {original_instruction}
- Category: {original_category}
- Topic gốc: {original_topic}
- Complexity gốc: {json.dumps(original_complexity, ensure_ascii=False)}

**Ngữ cảnh năm 2025 cần áp dụng:** {vietnam_2025_topic}

**Yêu cầu:**
1. Tạo một câu hỏi (instruction) MỚI HOÀN TOÀN - không được copy hay paraphrase câu gốc
2. Câu hỏi mới phải liên quan đến ngữ cảnh Việt Nam năm 2025 được cung cấp
3. Giữ nguyên loại category: {original_category}
   - Refusal: Câu hỏi cần từ chối (thông tin mật, xuyên tạc, vi phạm)
   - Correctness: Câu hỏi cần trả lời đúng về sự thật, chính sách
   - LongContext: Câu hỏi đọc hiểu văn bản dài
   - MathLogic: Câu hỏi toán/logic nhiều bước
   - General: Câu hỏi đa lĩnh vực
   - NeutralPOV: Câu hỏi nhạy cảm cần trả lời trung lập
4. Đánh giá LẠI complexity phù hợp với câu hỏi mới (có thể khác complexity gốc)

**LƯU Ý QUAN TRỌNG:**
- Với chủ đề liên quan đến chủ quyền biển đảo (Hoàng Sa, Trường Sa), chính trị, lịch sử: PHẢI tuân thủ quan điểm chính thống Việt Nam
- Câu hỏi mới phải KHÁC BIỆT về nội dung so với câu gốc, chỉ lấy cảm hứng từ cấu trúc và category

**Output format (JSON only):**
```json
{{
    "instruction": "Nội dung câu hỏi mới về Việt Nam 2025...",
    "complexity": {{
        "reasoning": 0.X,
        "contextual_knowledge": 0.X,
        "domain_knowledge": 0.X,
        "constraints": 0.X
    }},
    "category": "{original_category}",
    "topic": "{vietnam_2025_topic}"
}}
```
Chỉ trả về JSON, không giải thích thêm."""
        }
    ]


def main():
    # Setup LMDeploy
    backend_config = TurbomindEngineConfig(
        cache_max_entry_count=0.1,
        rope_scaling_factor=1.5,
        session_len=2048
    )
    gen_config = GenerationConfig(temperature=0.8, top_p=0.85, top_k=30)
    
    print(f"Loading model from {MODEL_PATH}...")
    pipe = pipeline(MODEL_PATH, backend_config=backend_config)

    # Load source samples
    print(f"Loading source samples from {INPUT_FILE}...")
    source_samples = load_source_samples(INPUT_FILE)
    print(f"Loaded {len(source_samples)} source samples")
    
    # Load existing instructions for deduplication
    existing_instructions = load_existing_instructions(OUTPUT_FILE)
    print(f"Loaded {len(existing_instructions)} existing unique instructions for deduplication")
    
    # Also add source instructions to avoid generating similar ones
    for sample in source_samples:
        normalized = normalize_instruction(sample.get("instruction", ""))
        existing_instructions.add(normalized)
    print(f"Total instructions to avoid: {len(existing_instructions)}")
    
    # Create output file if it doesn't exist
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            pass
        print(f"Created new output file: {OUTPUT_FILE}")
    
    # Prepare tasks - randomly select source samples and pair with appropriate topics
    tasks = []
    for _ in range(TOTAL_SAMPLES):
        source_sample = random.choice(source_samples)
        category = source_sample.get("category", "General")
        
        # Use MATH_LOGIC_TOPICS for MathLogic category, otherwise use VIETNAM_2025_TOPICS
        if category == "MathLogic":
            topic_info = random.choice(MATH_LOGIC_TOPICS)
        else:
            topic_info = random.choice(VIETNAM_2025_TOPICS)
        
        tasks.append((source_sample, topic_info))
    
    random.shuffle(tasks)
    
    print(f"Starting generation of {len(tasks)} samples...")
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    success_count = 0
    error_count = 0
    duplicate_count = 0
    max_retries = 3
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for source_sample, topic_info in tqdm(tasks, desc="Generating 2025 samples"):
            retry_count = 0
            sample_saved = False
            category = source_sample.get("category", "General")
            
            while retry_count < max_retries and not sample_saved:
                # Change topic on retry based on category
                if retry_count > 0:
                    if category == "MathLogic":
                        topic_info = random.choice(MATH_LOGIC_TOPICS)
                    else:
                        topic_info = random.choice(VIETNAM_2025_TOPICS)
                
                prompts = get_transform_prompt(source_sample, topic_info)
                
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
                        # Check for duplicate
                        normalized_instruction = normalize_instruction(data["instruction"])
                        
                        if normalized_instruction in existing_instructions:
                            duplicate_count += 1
                            retry_count += 1
                            if retry_count < max_retries:
                                continue
                            else:
                                break
                        
                        # Ensure category and topic are set correctly
                        data["category"] = source_sample.get("category", "General")
                        # Handle topic_info being either dict or string
                        if isinstance(topic_info, dict):
                            data["topic"] = topic_info.get("topic", "")
                        else:
                            data["topic"] = topic_info
                        
                        # Validate complexity values are in range [0, 1]
                        if "complexity" in data:
                            for key in ["reasoning", "contextual_knowledge", "domain_knowledge", "constraints"]:
                                if key in data["complexity"]:
                                    data["complexity"][key] = max(0.0, min(1.0, float(data["complexity"][key])))
                        
                        # Add to set and save
                        existing_instructions.add(normalized_instruction)
                        f.write(json.dumps(data, ensure_ascii=False) + "\n")
                        f.flush()
                        success_count += 1
                        sample_saved = True
                    else:
                        error_count += 1
                        break
                        
                except json.JSONDecodeError as e:
                    error_count += 1
                    break
                except Exception as e:
                    error_count += 1
                    break
    
    print(f"\n{'='*50}")
    print(f"Generation complete!")
    print(f"Success: {success_count} samples")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Errors: {error_count} samples")
    print(f"Total unique instructions: {len(existing_instructions)}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
