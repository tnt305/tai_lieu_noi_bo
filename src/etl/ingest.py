import sys
import os
from tqdm import tqdm

# Add project root to path để import được các module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.etl.chunkers import VNPTAIChunker
from src.etl.embedders import VNPTAIEmbedder
from src.rag.vectordb import VNPTAIVectorDB

def run_ingestion(batch_size: int = 10, upload_batch_size: int = 50):
    """
    ETL Pipeline với streaming embed để tránh OOM
    
    Args:
        batch_size: Model batch size cho embedding (default=8 cho GPU 10GB)
        upload_batch_size: Upload bao nhiêu chunks một lần vào DB (default=100)
    """
    # 1. KHỞI TẠO CÁC COMPONENT
    print("--- STEP 1: INITIALIZATION ---")
    chunker = VNPTAIChunker(dataset_path="src/etl/dataset")
    embedder = VNPTAIEmbedder()  # Model mặc định
    db = VNPTAIVectorDB(collection_name="360_xinchao")
    
    # 2. CHUNKING (Cắt nhỏ văn bản)
    print("\n--- STEP 2: SEMANTIC CHUNKING (Max 8192 chars) ---")
    chunks_obj = chunker.process_dataset_semantic(max_chars=8192)
    
    if not chunks_obj:
        print("## No chunks created. Check dataset path.")
        return

    print(f"## Created {len(chunks_obj)} chunks total")
    
    # 3. STREAMING EMBED + UPSERT (Tránh OOM)
    print(f"\n--- STEP 3: STREAMING EMBED & UPLOAD ---")
    print(f"## Batch size: {batch_size} (embedding) | {upload_batch_size} (upload)")
    
    # Đảm bảo collection tồn tại với đúng kích thước vector
    db.create_collection_if_not_exists(vector_size=embedder.dimension)
    
    total_chunks = len(chunks_obj)
    uploaded_count = 0
    
    # Process theo batches để streaming
    for i in tqdm(range(0, total_chunks, upload_batch_size), desc="## Upload batches", unit="batch"):
        # Lấy batch hiện tại
        batch_chunks = chunks_obj[i:i+upload_batch_size]
        
        # Convert sang dict
        chunks_dict = [c.to_dict() for c in batch_chunks]
        texts_to_embed = [c['content'] for c in chunks_dict]
        
        # Embed batch này (với batch_size nhỏ bên trong)
        print(f"\n  ## Embedding chunks {i+1}-{min(i+upload_batch_size, total_chunks)}...")
        vectors = embedder.embed(texts_to_embed, batch_size=batch_size)
        
        # Upload ngay vào DB
        db.upsert_chunks(chunks_dict, vectors)
        uploaded_count += len(chunks_dict)
        
        # Xóa biến để giải phóng memory
        del chunks_dict, texts_to_embed, vectors
        
        print(f"  ## Uploaded {uploaded_count}/{total_chunks} chunks")
    
    print(f"\n## INGESTION COMPLETED! Total: {uploaded_count} chunks indexed")

if __name__ == "__main__":
    # Có thể điều chỉnh batch_size nếu vẫn OOM:
    run_ingestion(batch_size=4)
    # run_ingestion()