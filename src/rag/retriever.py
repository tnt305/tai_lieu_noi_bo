from typing import List, Dict, Optional
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.rag.vectordb import VNPTAIVectorDB
from src.etl.embedders import VNPTAIEmbedder


class VNPTAIRetriever:
    """
    RAG Retriever - Tìm kiếm document chunks relevant với user query
    """
    
    def __init__(
        self, 
        collection_name: str = "360_xinchao",
        embedder_model: str = "vnptai_hackathon_embedding"

    ):
        """
        Args:
            collection_name: Tên collection trong Qdrant
            embedder_model: Model để embed query (phải giống model khi ingest)
        """
        print("🔧 Initializing RAG Retriever...")
        self.db = VNPTAIVectorDB(collection_name=collection_name)
        self.embedder = VNPTAIEmbedder(model_name=embedder_model)
        print("✅ Retriever ready!")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        chunk_type: Optional[str] = None,
        doc_title: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Tìm kiếm chunks relevant với query
        
        Args:
            query: Câu hỏi của user (tiếng Việt)
            top_k: Số lượng chunks trả về
            chunk_type: Lọc theo loại chunk ('dieu', 'khoan', 'summary')
            doc_title: Lọc theo tên văn bản cụ thể
            min_score: Score tối thiểu (0-1) để filter kết quả
            
        Returns:
            List of dicts chứa {content, metadata, score}
        """
        print(f"\n🔍 Searching for: '{query}'")
        
        # 1. Embed query thành vector
        query_vector = self.embedder.embed([query])[0]
        
        # 2. Build filter nếu cần
        search_filter = None
        if chunk_type or doc_title:
            conditions = []
            if chunk_type:
                conditions.append(
                    FieldCondition(key="type", match=MatchValue(value=chunk_type))
                )
            if doc_title:
                conditions.append(
                    FieldCondition(key="doc_title", match=MatchValue(value=doc_title))
                )
            search_filter = Filter(must=conditions)
        
        # 3. Search trong Qdrant
        results = self.db.search(
            query_vector=query_vector, 
            limit=top_k,
            query_filter=search_filter
        )
        
        # 4. Format kết quả
        formatted_results = []
        for hit in results:
            # Filter theo min_score
            if hit.score < min_score:
                continue
                
            formatted_results.append({
                'content': hit.payload.get('original_content', ''),  # Nội dung gốc
                'metadata': {
                    'doc_title': hit.payload.get('doc_title'),
                    'source_url': hit.payload.get('source_url'),
                    'type': hit.payload.get('type'),
                    'dieu_so': hit.payload.get('dieu_so'),
                    'khoan_so': hit.payload.get('khoan_so'),
                },
                'score': round(hit.score, 4),
                'id': hit.id
            })
        
        print(f"✅ Found {len(formatted_results)} relevant chunks")
        return formatted_results
    
    def search_with_context(
        self, 
        query: str, 
        top_k: int = 3,
        **kwargs
    ) -> str:
        """
        Tìm kiếm và format thành context cho LLM
        
        Returns:
            String formatted context ready để đưa vào LLM prompt
        """
        results = self.search(query, top_k=top_k, **kwargs)
        
        if not results:
            return "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
        
        # Format thành context string
        context_parts = []
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            context_parts.append(
                f"[Nguồn {i}] {meta['doc_title']}\n"
                f"URL: {meta['source_url']}\n"
                f"{result['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_document_structure(self, doc_title: str) -> Dict:
        """
        Lấy cấu trúc của một văn bản cụ thể (các Điều, Khoản)
        
        Args:
            doc_title: Tên văn bản (ví dụ: "Nghị định 68/2019/NĐ-CP")
            
        Returns:
            Dict chứa structure của văn bản
        """
        # Search summary chunk của văn bản
        summary = self.search(
            query=doc_title, 
            top_k=1, 
            chunk_type='summary',
            doc_title=doc_title
        )
        
        # Search all điều của văn bản
        dieu_chunks = self.db.client.scroll(
            collection_name=self.db.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="doc_title", match=MatchValue(value=doc_title)),
                    FieldCondition(key="type", match=MatchValue(value="dieu"))
                ]
            ),
            limit=100
        )
        
        return {
            'summary': summary[0] if summary else None,
            'total_dieu': len(dieu_chunks[0]) if dieu_chunks else 0,
            'dieu_list': [
                f"Điều {chunk.payload.get('dieu_so')}" 
                for chunk in (dieu_chunks[0] if dieu_chunks else [])
            ]
        }
