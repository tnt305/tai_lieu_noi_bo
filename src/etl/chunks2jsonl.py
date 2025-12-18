import sys
import os
import json
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.etl.chunkers import VNPTAIChunker

def export_chunks_to_jsonl(output_path: str = "chunks_output.jsonl"):
    """
    Export chunks ra file JSONL để backup hoặc debug
    """
    print("--- CHUNKING & EXPORT TO JSONL ---")
    chunker = VNPTAIChunker(dataset_path="src/etl/dataset")
    chunks_obj = chunker.process_dataset()
    
    if not chunks_obj:
        print("❌ No chunks created.")
        return
    
    print(f"\n📝 Exporting {len(chunks_obj)} chunks to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in tqdm(chunks_obj, desc="💾 Writing JSONL", unit="chunk"):
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
    
    print(f"✅ Exported to {output_path}")
    
    # In thống kê
    chunk_types = {}
    for c in chunks_obj:
        chunk_types[c.type] = chunk_types.get(c.type, 0) + 1
    
    print("\n📊 Chunk Statistics:")
    for ctype, count in sorted(chunk_types.items()):
        print(f"  - {ctype}: {count} chunks")

if __name__ == "__main__":
    export_chunks_to_jsonl()
