# QA System - AIO-Hitman

Hệ thống Hỏi đáp Tự động (QA System) sử dụng kiến trúc RAG (Retrieval-Augmented Generation) kết hợp với Router thông minh và quy trình suy luận đa bước (Multi-step Reasoning) để giải quyết các câu hỏi trắc nghiệm đa lĩnh vực.

## 1. Pipeline Flow

Sơ đồ luồng xử lý của hệ thống:

### Sơ đồ luồng xử lý (Architecture)

![Architecture Flowchart](figs/vnptai.png)

#### Chi tiết Luồng xử lý:

![Logical Flow](figs/logical.png)
*Sơ đồ luồng xử lý Logic (Math/Science)*

![Context Retrieval](figs/context_retrieval.png)
*Sơ đồ luồng truy xuất ngữ cảnh (RAG)*

**Mô tả chi tiết:**
1.  **Input Processing**: Câu hỏi được kiểm tra an toàn (Safety Check) và lọc qua lớp **Correction Rules** (sử dụng Qdrant để tìm các lỗi sai tiền lệ và đưa ra gợi ý sửa lỗi).
2.  **Intent Routing**: Phân loại câu hỏi thành 2 luồng chính:
    *   **Logical Path (Math/Science)**: Dành cho các câu hỏi cần suy luận toán học, vật lý hoặc tư duy logic.
    *   **Context Retrieval Path (RAG/Knowledge)**: Dành cho các câu hỏi cần tra cứu kiến thức pháp luật, lịch sử, xã hội.
3.  **Logical Path**:
    *   Sử dụng Large LLM để sinh ra **Rationale** (Chuỗi suy nghĩ) và **Program** (Code Python).
    *   Thực thi code Python để có kết quả chính xác tuyệt đối (tránh hallucination khi tính toán).
    *   Sử dụng cơ chế **Voting Ensemble** từ 3 Small LLM experts để thẩm định kết quả cuối cùng.
4.  **Context Retrieval Path (RAG)**:
    *   Truy vấn đa tầng từ Qdrant VectorDB (Semantic Search).
    *   **Re-ranking**: Đánh giá lại độ phù hợp của tài liệu tìm được.
    *   **Adaptive Answering**: Tự động chọn Small LLM (cho câu dễ/có context tốt) hoặc Large LLM (cho câu khó/suy luận phức tạp) để tối ưu chi phí và độ chính xác.
5.  **Final Verification**: Kiểm tra lại định dạng và tính hợp lý của đáp án trước khi xuất kết quả.

## 2. Data Processing

Quy trình xử lý dữ liệu được thực hiện qua module `src/etl`:

1.  **Thu thập dữ liệu (Crawling)**:
    *   Sử dụng `src/crawler` để tải văn bản pháp luật và Wikipedia.
    *   Công cụ: `Trafilatura` để extract content sạch, loại bỏ các thành phần rác của HTML.

2.  **Làm sạch & Chuẩn hóa**:
    *   Xóa bỏ các citation marker (`[1]`, `[edit]`), các link rác.
    *   Chuẩn hóa encoding và định dạng Markdown.
    *   Logic nằm trong `src/etl/chunkers.py` -> `_clean_wiki_content`.

3.  **Chunking**:
    *   Sử dụng **Semantic Chunking**: Cắt văn bản dựa trên cấu trúc ngữ nghĩa (Chương, Điều, Khoản).
    *   **Context Injection**: Mỗi chunk con đều được gắn kèm Tiêu đề và Context của văn bản mẹ để đảm bảo ngữ nghĩa độc lập khi tìm kiếm.
    *   Độ dài chunk tối đa: 8192 characters (hoặc tùy chỉnh để phù hợp context window).

4.  **Embedding**:
    *   Sử dụng mô hình embedding qua API (`vnptai_hackathon_embedding`).
    *   Dữ liệu được vector hóa và chuẩn hóa dimension.

## 3. Resource Initialization

Hướng dẫn khởi tạo tài nguyên để chạy pipeline:

### Bước 1: Cài đặt môi trường
```bash
pip install -r requirements.txt
```

### Bước 2: Ingestion (Khởi tạo Database)
Chạy script ETL để xử lý dữ liệu thô và đẩy vào Qdrant:
```bash
python src/etl/ingest.py
```
*Lưu ý: qdrant được lưu dưới dạng sqlite storage tại `qdrant_data` folder. Main Collection là 360_xinchao*

### Bước 3: Chạy Inference với Docker

#### 3.1 Setup Environment
Tạo file `.env` từ template và điền các API Key/URL cần thiết:
```bash
    LLM_SMALL_AUTH=
    LLM_SMALL_TOKEN_ID=
    LLM_SMALL_TOKEN_KEY=
    LLM_SMALL_API_NAME=

    LLM_LARGE_AUTH=
    LLM_LARGE_TOKEN_ID=
    LLM_LARGE_TOKEN_KEY=
    LLM_LARGE_API_NAME=

    LLM_EMBED_AUTH=
    LLM_EMBED_TOKEN_ID=
    LLM_EMBED_TOKEN_KEY=
    LLM_EMBED_API_NAME=
```

#### 3.2 Docker Run
1. **Build Image** (nếu chưa có hoặc khi sừa code):
```bash
docker build -t team_submission .
```

2. **Run Container**:
Lệnh sau sẽ mount thư mục hiện tại vào container để:
- Sử dụng file `dataset/test.json` làm input.
- Lưu kết quả `submission.csv` ra ngoài máy thật.

```bash
docker run --rm \
  -v "${PWD}/dataset/test.json:/code/dataset/test.json" \
  -v "${PWD}:/code" \
  team_submission
```

Kết quả sẽ được lưu tại:
*   `submission.csv`: File nộp bài (id, answer).
*   `submission_time.csv`: File theo dõi thời gian (id, answer, time).

### Bước 4: 
Notes: Ngoài các module cơ bản, còn một module nữa về caching, nó được lưu tại `dataset/semantic_cache.pkl`
- Ý tưởng của module này là để giảm thiểu lượng query gửi ra Qdrant, khi có query trùng lặp, ta sẽ tìm kiếm trong cache trước, nếu có thì trả về kết quả ngay, không cần query lại Qdrant. Các thông tin, logical process được verify sử dụng validation set.
- Target rằng, tối ưu dựa trên validation, chứ không cố gắng build massive qdrant database, điều này sẽ đảm bảo đánh giá hiệu quả nhất với chất lượng mô hình sinh
- Cách tiếp cận của tôi dựa trên thực nghiệm từ các nghiên cứu trước + Agent hiện tại đang được users sử dụng, răng càng nhỏ càng tốt (nhỏ mà có võ), vậy nên cách tiếp cận sẽ được triển khai theo hướng Distillation, nhằm học các tri thức từ một mô hình lớn cho các tác vụ reasoning phức tạp, còn để các tác vụ đơn giản thì để các mô hình nhỏ tự thân.
- Routing models: Các mô hình được nén onnx và lưu tại `models/` để không bị lệ thuộc vào các thay đổi về môi trường. Chi tiết xem tại `config.json`
