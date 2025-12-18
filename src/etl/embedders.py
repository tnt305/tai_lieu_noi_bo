from typing import List
import requests
from src import load_llm_config
import time
from tqdm import tqdm

class VNPTAIEmbedder:
    def __init__(self, model_name: str = "vnptai_hackathon_embedding"):
        """
        Initialize Embedding API client
        
        Args:
            model_name: Name of the model to use (default: vnptai_hackathon_embedding)
        """
        print(f"🔄 Initializing API embedder: {model_name}...")
        self.config = load_llm_config("embeddings")
        self.model_name = model_name
        self.api_url = "https://api.idg.vnpt.vn/data-service/vnptai-hackathon-embedding"
        
        # Determine dimension (defaulting to 1024 to match BGE-M3 legacy)
        # Note: You might want to verify this by making a test call
        self._dimension = 1024
        
    def embed(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Embed texts using VNPT AI API with batching and rate limiting.
        Quota: 500 embeddings / minute (~8.33/sec)
        
        Args:
            texts: List of strings to embed
            batch_size: Number of texts to send in one API call
            
        Returns:
            List of embedding vectors
        """
        headers = { 
           'Authorization': self.config.get('authorization', ''), 
           'Token-id': self.config.get('tokenId', ''), 
           'Token-key': self.config.get('tokenKey', ''), 
           'Content-Type': 'application/json', 
        } 
        
        results = []
        
        # Calculate delay to respect quota: 500 items/minute => 0.12s per item
        # We wait to ensure we don't exceed rate limit
        time_per_item = 60.0 / 500.0
        
        for i in range(0, len(texts), batch_size):
            start_time = time.time()
            batch_texts = texts[i : i + batch_size]
            
            # Safety Truncation: Fix 500 Internal Server Error for large files
            # User requirement: Max 8192 chars.
            safe_batch_texts = []
            for text in batch_texts:
                if len(text) > 8192:
                    print(f"⚠️ Truncating text from {len(text)} to 8192 chars to avoid API Error.")
                    safe_batch_texts.append(text[:8192])
                else:
                    safe_batch_texts.append(text)
            
            current_batch_size = len(safe_batch_texts)
             
            json_data = { 
                'model': self.model_name, 
                'input': safe_batch_texts, 
                'encoding_format': 'float', 
            } 
             
            # Robust Retry Loop for Timeouts
            max_retries = 10  # Try up to 10 times to avoid infinite hangs on bad logic, but functionally "keep running"
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.api_url, 
                        headers=headers, 
                        json=json_data,
                        timeout=120
                    )
                    
                    # If 4xx error (client side), typical raise_for_status might act different
                    # but usually we want to crash on 400 (bad request) vs retry on 500/timeout
                    if 400 <= response.status_code < 500:
                        print(f"❌ Client Error {response.status_code}: {response.text}")
                        response.raise_for_status() 

                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract embeddings
                    batch_res = data['data']
                    for item in batch_res:
                        results.append(item['embedding'])
                    
                    # Success -> Break retry loop
                    break
                    
                except Exception as e:
                    print(f"⚠️ Embedding API error for batch index {i} (Attempt {attempt+1}/{max_retries}): {e}")
                    
                    if hasattr(e, 'response') and e.response is not None:
                         print(f"❌ Server Response: {e.response.text}")

                    # User requested: Wait 60s and continue running (retry)
                    if attempt < max_retries - 1:
                        print(f"   ⏳ Waiting 60s before retrying current batch...")
                        for _ in tqdm(range(60), desc="Retry Wait"):
                            time.sleep(1)
                    else:
                        print(f"❌ Failed after {max_retries} attempts.")
                        raise e
            
            # Rate limiting check
            elapsed = time.time() - start_time
            required_time = current_batch_size * time_per_item
            if elapsed < required_time:
                time.sleep(required_time - elapsed)
                
        return results
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension