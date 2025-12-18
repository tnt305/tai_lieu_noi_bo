
import sys
import os
import time
from tqdm import tqdm
from datasets import load_from_disk, Dataset
from typing import List, Dict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.etl.chunkers import VNPTAIChunker, Chunk
from src.etl.embedders import VNPTAIEmbedder
from src.rag.vectordb import VNPTAIVectorDB

def ingest_external_dataset(
    dataset_path_or_obj, 
    batch_size: int = 10,       # Batch size cho embedding (quota 500/min)
    upload_batch_size: int = 800 # Batch size cho upload DB
):
    """
    Ingest dataset custom vào VNPT AI Vector DB.
    
    Args:
        dataset_path_or_obj: Path tới HF dataset saved on disk HOẶC object Dataset
    """
    
    # 1. INITIALIZATION
    print("--- STEP 1: INITIALIZATION ---")
    chunker = VNPTAIChunker(dataset_path="src/etl/dataset") # Path ko quan trọng ở mode này
    embedder = VNPTAIEmbedder()
    db = VNPTAIVectorDB(collection_name="360_xinchao")
    
    # Load dataset nếu là path
    if isinstance(dataset_path_or_obj, str):
        print(f"📂 Loading dataset from: {dataset_path_or_obj}")
        ds = load_from_disk(dataset_path_or_obj)
    else:
        ds = dataset_path_or_obj
        
    print(f"📊 Dataset info: {len(ds)} rows")
    
    # Ensure collection exists
    db.create_collection_if_not_exists(vector_size=embedder.dimension)
    
    # 2. STREAMING PROCESS (Chunk -> Embed -> Upload)
    # Vì dataset lớn (1.2M rows), ta không tạo list chunk khổng lồ mà làm cuốn chiếu.
    
    buffer_chunks: List[Dict] = []
    total_uploaded = 0
    
    print("\n--- STEP 2: STREAMING INGESTION ---")
    
    for row in tqdm(ds, desc="Processing rows"):
        # A. CHUNKING
        # row: {'id', 'revid', 'url', 'title', 'text'}
        try:
            item_chunks: List[Chunk] = chunker.process_external_item(row)
            
            # Convert to dict for DB
            for c in item_chunks:
                buffer_chunks.append(c.to_dict())
                
        except Exception as e:
            print(f"⚠️ Error processing row {row.get('id', '?')}: {e}")
            continue
            
        # B. BATCH UPLOAD CHECK
        if len(buffer_chunks) >= upload_batch_size:
            _process_buffer(buffer_chunks, embedder, db, batch_size)
            total_uploaded += len(buffer_chunks)
            buffer_chunks = [] # Clear buffer
            
    # Process remaining chunks
    if buffer_chunks:
        _process_buffer(buffer_chunks, embedder, db, batch_size)
        total_uploaded += len(buffer_chunks)
        
    print(f"\n✅ INGESTION COMPLETED! Total chunks indexed: {total_uploaded}")

def _process_buffer(chunks_list: List[Dict], embedder, db, batch_size):
    """Helper để embed và upload một batch chunks"""
    if not chunks_list:
        return
        
    texts_to_embed = [c['content'] for c in chunks_list]
    
    # Embed (Hàm embedder đã có logic batching + rate limit bên trong)
    # Tuy nhiên ta truyền batch_size vào để nó chia nhỏ tiếp khi gọi API
    try:
        vectors = embedder.embed(texts_to_embed, batch_size=batch_size)
        
        # Upload
        if len(vectors) == len(chunks_list):
            db.upsert_chunks(chunks_list, vectors)
        else:
            print(f"❌ Mismatch detected: {len(chunks_list)} chunks but {len(vectors)} vectors.")
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")

if __name__ == "__main__":
    # Load HuggingFace dataset directly (USER REQUESTED)
    from datasets import load_dataset
    print("🚀 Loading dataset 'vietgpt/wikipedia_vi' from HuggingFace...")
    ds = load_dataset("vietgpt/wikipedia_vi", split="train") 
    
    # Run ingestion
    ingest_external_dataset(ds)
