"""
CorrectionBank with Qdrant Integration
Stores correction rules in Qdrant for efficient vector search (like RAG).

Usage:
    # 1. Upload existing rules to Qdrant
    python -m src.rag.correction_qdrant upload
    
    # 2. Use in inference (automatic)
    # CorrectionBank will query Qdrant for similar past errors
"""

import os
import json
import requests
import numpy as np
from typing import Dict, List, Optional
import time

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue
)
import uuid

from src import load_llm_config
from src.etl.embedders import VNPTAIEmbedder
from src.rag.vectordb import _GLOBAL_QDRANT_CLIENT, VNPTAIVectorDB


class CorrectionBankQdrant:
    """
    CorrectionBank using Qdrant for persistent vector storage.
    Acts like RAG - query similar past errors to get correction tips.
    """
    
    COLLECTION_NAME = "correction_rules"
    VECTOR_SIZE = 1024  # BGE-m3 embedding dimension
    
    def __init__(
        self, 
        qdrant_path: str = "./qdrant_data",
        threshold: float = 0.75,
        embedder: Optional[VNPTAIEmbedder] = None
    ):
        self.threshold = threshold
        self.qdrant_path = qdrant_path
        
        # Use shared global client from vectordb module to avoid lock contention
        # If accessing protected member is an issue, we should expose it properly,
        # but for now we import the variable.
        # We need to check if it is initialized, if not, we initialize it via VNPTAIVectorDB or manually.
        
        from src.rag.vectordb import _GLOBAL_QDRANT_CLIENT as shared_client
        import src.rag.vectordb as vdb_module
        
        if shared_client is None:
            print(f"📦 Initializing Shared Qdrant Client (from CorrectionBank)...")
            client = QdrantClient(path=qdrant_path)
            vdb_module._GLOBAL_QDRANT_CLIENT = client
            self.client = client
        else:
            self.client = shared_client
            
        # Embedder (shared with main system if provided)
        self.embedder = embedder
        
        # LLM Config for Reflexion
        self.large_config = load_llm_config('large')
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if not exists"""
        if not self.client.collection_exists(self.COLLECTION_NAME):
            print(f"📦 Creating Qdrant collection '{self.COLLECTION_NAME}'...")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE, 
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{self.COLLECTION_NAME}' created.")
        else:
            # Get collection info
            info = self.client.get_collection(self.COLLECTION_NAME)
            print(f"✅ Qdrant CorrectionBank: {info.points_count} rules loaded")
    
    def lookup(
        self, 
        query_vector: List[float], 
        context_hash: str = None,
        top_k: int = 1
    ) -> Optional[str]:
        """
        Find applicable correction rules for similar past errors.
        Returns the correction_tip if found, None otherwise.
        
        Args:
            query_vector: Embedding of current query
            context_hash: Optional hash to filter by context
            top_k: Number of similar rules to consider
            
        Returns:
            correction_tip string or None
        """
        try:
            # Build filter if context_hash provided
            search_filter = None
            if context_hash:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="context_hash", 
                            match=MatchValue(value=context_hash)
                        )
                    ]
                )
            
            # Search in Qdrant using query_points (new API)
            results = self.client.query_points(
                collection_name=self.COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
                query_filter=search_filter
            )
            
            # If no results with context filter, try without
            if not results.points and context_hash:
                results = self.client.query_points(
                    collection_name=self.COLLECTION_NAME,
                    query=query_vector,
                    limit=top_k
                )
            
            if results.points:
                best_hit = results.points[0]
                if best_hit.score >= self.threshold:
                    correction_tip = best_hit.payload.get('correction_tip', '')
                    print(f"📖 Found Correction Rule (Qdrant, Score: {best_hit.score:.3f})")
                    return correction_tip
            
            return None
            
        except Exception as e:
            print(f"⚠️ CorrectionBank Qdrant lookup error: {e}")
            return None
    
    def add_rule(
        self,
        query: str,
        query_vector: List[float],
        correction_tip: str,
        wrong_answer: str,
        correct_answer: str,
        intent: str,
        context_hash: str = None
    ):
        """
        Add a new correction rule to Qdrant.
        
        Args:
            query: Original question
            query_vector: Embedding vector
            correction_tip: The correction tip text
            wrong_answer: What model predicted (wrong)
            correct_answer: The correct answer
            intent: Category (MathLogic, Correctness, etc.)
            context_hash: Optional context hash
        """
        try:
            # Generate deterministic UUID from query
            namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
            point_id = uuid.uuid5(namespace, query)
            
            # Payload for Qdrant
            payload = {
                'query': query,
                'correction_tip': correction_tip,
                'wrong_answer': wrong_answer,
                'correct_answer': correct_answer,
                'intent': intent,
                'context_hash': context_hash,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=str(point_id),
                        vector=query_vector,
                        payload=payload
                    )
                ]
            )
            
            print(f"✅ Added rule to Qdrant: {correction_tip[:50]}...")
            
        except Exception as e:
            print(f"⚠️ Failed to add rule to Qdrant: {e}")
    
    def upload_from_jsonl(self, jsonl_file: str = "dataset/correction_rules.jsonl"):
        """
        Upload existing rules from JSONL file to Qdrant.
        This is a one-time migration to populate Qdrant.
        """
        if not os.path.exists(jsonl_file):
            print(f"❌ JSONL file not found: {jsonl_file}")
            return
        
        # Initialize embedder if not provided
        if not self.embedder:
            print("🔧 Initializing embedder for upload...")
            self.embedder = VNPTAIEmbedder()
        
        # Read JSONL
        rules = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    rules.append(json.loads(line.strip()))
        
        if not rules:
            print("❌ No rules found in JSONL file")
            return
        
        print(f"📂 Found {len(rules)} rules to upload")
        
        # Embed all queries
        queries = [rule['query'] for rule in rules]
        print("🔄 Embedding queries...")
        vectors = self.embedder.embed(queries)
        
        # Upload to Qdrant
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        points = []
        
        for i, (rule, vector) in enumerate(zip(rules, vectors)):
            point_id = uuid.uuid5(namespace, rule['query'])
            
            payload = {
                'query': rule['query'],
                'correction_tip': rule['correction_tip'],
                'wrong_answer': rule.get('reasoning', {}).get('wrong_answer_text', ''),
                'correct_answer': rule.get('reasoning', {}).get('correct_answer', ''),
                'intent': rule.get('metadata', {}).get('intent', 'General'),
                'context_hash': rule.get('metadata', {}).get('context_hash'),
                'timestamp': rule.get('metadata', {}).get('timestamp', '')
            }
            
            points.append(PointStruct(
                id=str(point_id),
                vector=vector,
                payload=payload
            ))
        
        # Batch upsert
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )
        
        print(f"✅ Uploaded {len(points)} rules to Qdrant collection '{self.COLLECTION_NAME}'")
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        info = self.client.get_collection(self.COLLECTION_NAME)
        return {
            'total_rules': info.points_count,
            'collection_name': self.COLLECTION_NAME,
            'vector_size': self.VECTOR_SIZE,
            'status': info.status
        }


def main():
    """CLI for CorrectionBank Qdrant operations"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.rag.correction_qdrant upload    # Upload JSONL to Qdrant")
        print("  python -m src.rag.correction_qdrant stats     # Show collection stats")
        print("  python -m src.rag.correction_qdrant test      # Test lookup")
        return
    
    command = sys.argv[1]
    bank = CorrectionBankQdrant()
    
    if command == "upload":
        jsonl_file = sys.argv[2] if len(sys.argv) > 2 else "dataset/correction_rules.jsonl"
        bank.upload_from_jsonl(jsonl_file)
        
    elif command == "stats":
        stats = bank.get_stats()
        print(f"\n📊 CorrectionBank Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    elif command == "test":
        # Test with a sample query
        from src.etl.embedders import VNPTAIEmbedder
        embedder = VNPTAIEmbedder()
        
        test_query = "Ngôi chùa Ba La Mật được khai dựng vào năm nào?"
        vector = embedder.embed([test_query])[0]
        
        tip = bank.lookup(vector)
        if tip:
            print(f"\n✅ Found correction tip:")
            print(f"   {tip}")
        else:
            print("\n❌ No matching rule found")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
