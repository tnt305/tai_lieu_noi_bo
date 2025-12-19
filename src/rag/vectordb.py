from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import uuid

# Global singleton client
# Global singleton client
_GLOBAL_QDRANT_CLIENT = None

# --- HOTFIX: Patch Qdrant Client to allow extra fields (Fix Pydantic V2 Error) ---
try:
    from qdrant_client.http import models as rest_models
    # Force 'extra' to 'allow' for CreateCollection to ignore unexpected None fields
    if hasattr(rest_models.CreateCollection, 'model_config'):
        rest_models.CreateCollection.model_config['extra'] = 'allow'
        # CRITICAL for Pydantic V2: Rebuild the model to apply config changes
        rest_models.CreateCollection.model_rebuild(force=True)
        print("🔧 Qdrant Client patched: CreateCollection now allows extra fields (Rebuilt).")
except ImportError:
    pass
# ---------------------------------------------------------------------------------


class VNPTAIVectorDB:
    def __init__(self, collection_name: str = "vnptai_xinchao", path: str = "./qdrant_data"):
        global _GLOBAL_QDRANT_CLIENT
        
        # path="./qdrant_data" giúp lưu dữ liệu xuống ổ cứng, tắt code đi bật lại vẫn còn
        if _GLOBAL_QDRANT_CLIENT is None:
            print(f"📦 Initializing Global Qdrant Client at {path}...")
            _GLOBAL_QDRANT_CLIENT = QdrantClient(path=path)
        
        self.client = _GLOBAL_QDRANT_CLIENT
        self.collection_name = collection_name

    def create_collection_if_not_exists(self, vector_size: int):
        """Tạo collection nếu chưa có"""
        if not self.client.collection_exists(self.collection_name):
            print(f"📦 Creating collection '{self.collection_name}' with size {vector_size}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        else:
            print(f"✅ Collection '{self.collection_name}' already exists.")

    def upsert_chunks(self, chunks: List[Dict], vectors: List[List[float]]):
        """
        Đẩy dữ liệu vào DB.
        chunks: List các dict (kết quả từ chunk.to_dict())
        vectors: List các vector tương ứng
        """
        points = []
        # Namespace UUID để tạo deterministic UUID từ string ID
        NAMESPACE_VNPTAI = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        
        for chunk, vector in zip(chunks, vectors):
            # Payload là nơi chứa metadata để lọc (ví dụ: tìm điều 1 của văn bản X)
            payload = chunk  # Lưu toàn bộ thông tin chunk vào payload
            
            # Convert string ID to UUID using uuid5 (deterministic, SHA-1 based)
            # Ví dụ: "390b669ade689766_summary" -> UUID("...")
            chunk_uuid = uuid.uuid5(NAMESPACE_VNPTAI, chunk['id'])
            
            points.append(PointStruct(
                id=chunk_uuid,  # UUID tạo từ string ID (deterministic)
                vector=vector,
                payload=payload
            ))

        # Upload theo batch để tối ưu
        operation_info = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )
        print(f"🚀 Upserted {len(points)} points. Status: {operation_info.status}")

    def search(self, query_vector: List[float], limit: int = 5, query_filter=None):
        """
        Hàm search trong vector database
        
        Args:
            query_vector: Vector của query
            limit: Số lượng kết quả trả về
            query_filter: Qdrant Filter object để lọc kết quả
        """
        # Try new API first (1.8+), fallback to old API if not available
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            return results.points if hasattr(results, 'points') else results
        except (AttributeError, TypeError):
            # Fallback to old API
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )