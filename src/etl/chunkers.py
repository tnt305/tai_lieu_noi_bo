import re
import json
import os
from typing import List, Dict
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from tqdm import tqdm

# Thư viện NLP tiếng Việt
try:
    from underthesea import pos_tag
except ImportError:
    raise ImportError("Vui lòng cài đặt: pip install underthesea")

@dataclass
class Chunk:
    id: str                 # Unique ID: {file_hash}_{local_id}
    doc_id: str             # file_hash
    type: str               # dieu, khoan, topic, entity
    content: str            # Nội dung để embed (có context)
    original_content: str   # Nội dung gốc (để hiển thị cho user)
    metadata: Dict          # Metadata phong phú
    keywords: List[str]     # NLP extracted
    
    def to_dict(self):
        return asdict(self)

    @staticmethod
    def split_text_with_overlap(text: str, max_chars: int = 8192, overlap: int = 1024) -> List[str]:
        """
        Chia nhỏ text nếu quá dài, có gối đầu (overlap) để giữ ngữ cảnh.
        Dùng max_chars để ước lượng (1500 chars ~ 300-400 tokens an toàn).
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            
            # Cố gắng cắt ở khoảng trắng gần nhất để không gãy từ
            if end < len(text):
                # Tìm khoảng trắng gần nhất ngược từ end
                verify_limit = 100 # Chỉ lùi lại tối đa 100 chars để tìm điểm cắt
                found_space = False
                for i in range(end, end - verify_limit, -1):
                    if text[i].isspace():
                        end = i
                        found_space = True
                        break
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(chunk_content)
            
            # Di chuyển cửa sổ trượt, lùi lại một đoạn overlap
            start = end - overlap
            
            # Tránh vòng lặp vô tận nếu overlap >= max_chars hoặc không tiến triển
            if start >= end: 
                start = end # Force move if stuck
                
        return chunks

class VNPTAIChunker:
    def __init__(self, dataset_path: str = "src/etl/dataset"):
        """
        Args:
            dataset_path: Đường dẫn đến folder chứa file_mapping.json và các file .md
        """
        self.dataset_path = Path(dataset_path)
        self.mapping_file = self.dataset_path / "file_mapping.json"
        
        # Regex Patterns (Giữ nguyên logic tốt của bản cũ)
        self.patterns = {
            'chuong': r'\*\*Chương ([IVX\d]+)\*\*\s*\n\n\*\*(.+?)\*\*',
            'dieu': r'\*\*Điều (\d+)\.\*\*\s*(.+?)(?=\n)',
            'khoan': r'^(\d+)\.\s+(.+?)$',
            'org_detect': r'(?:Ủy ban nhân dân|UBND|Sở|Bộ|Ban|Chính phủ|Quốc hội)(?:\s+[A-ZĐĂÂÊÔƠƯ][a-zđăâêôơư]+)+',
        }
        
        # Cache stopwords nếu cần
        self.stopwords = {'của', 'và', 'các', 'những', 'đối', 'với', 'trong'}

    def process_dataset(self) -> List[Chunk]:
        """Hàm chính để chạy ETL pipeline"""
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Không tìm thấy {self.mapping_file}")

        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            file_mapping = json.load(f)

        all_chunks = []
        
        print(f"## Bắt đầu xử lý {len(file_mapping)} văn bản...")
        
        for file_hash, meta in tqdm(file_mapping.items(), desc="Processing documents", unit="doc"):
            md_file_path = self.dataset_path / meta['file']
            
            if not md_file_path.exists():
                print(f"## Warning: Missing file {meta['file']}")
                continue
                
            # Đọc nội dung file Markdown
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Tạo metadata gốc cho từng chunk
            base_metadata = {
                'source_url': meta['url'],
                'doc_title': meta['title'],
                'file_hash': file_hash
            }
            
            # Xử lý từng file
            doc_chunks = self._parse_single_document(file_hash, content, base_metadata)
            all_chunks.extend(doc_chunks)
            
        print(f"✅ Hoàn tất! Đã tạo ra {len(all_chunks)} chunks.")
        return all_chunks

    def process_dataset_no_chunking(self) -> List[Chunk]:
        """
        Xử lý dataset nhưng giữ nguyên toàn bộ nội dung file làm 1 chunk.
        Dùng cho payload embedding lớn hoặc model hỗ trợ context dài.
        """
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Không tìm thấy {self.mapping_file}")

        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            file_mapping = json.load(f)

        all_chunks = []
        print(f"## Bắt đầu xử lý {len(file_mapping)} văn bản (NO CHUNKING MODE)...")
        
        for file_hash, meta in tqdm(file_mapping.items(), desc="Processing documents", unit="doc"):
            md_file_path = self.dataset_path / meta['file']
            
            if not md_file_path.exists():
                print(f"## Warning: Missing file {meta['file']}")
                continue
                
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Tạo 1 chunk duy nhất cho cả file
            chunk = Chunk(
                id=file_hash,
                doc_id=file_hash,
                type='full_doc',
                content=content,
                original_content=content,
                metadata={
                    'source_url': meta['url'],
                    'doc_title': meta['title'],
                    'file_hash': file_hash,
                    'is_full_doc': True
                },
                keywords=[] # Bỏ qua NLP
            )
            all_chunks.append(chunk)
            
        print(f"✅ Hoàn tất! Đã tạo ra {len(all_chunks)} full-doc chunks.")
        return all_chunks

        return all_chunks

    def process_dataset_semantic(self, max_chars: int = 8192) -> List[Chunk]:
        """
        Semantic Chunking (Simplified):
        - Gom nhóm các đoạn văn (paragraphs) lại với nhau.
        - Tôn trọng ranh giới \n\n để không cắt giữa chừng câu/ý.
        - Đảm bảo kích thước chunk <= max_chars (default 8192).
        """
        if not self.mapping_file.exists():
            raise FileNotFoundError(f"Không tìm thấy {self.mapping_file}")

        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            file_mapping = json.load(f)

        all_chunks = []
        print(f"## Bắt đầu Semantic Chunking (Context: {max_chars} chars)...")
        
        for file_hash, meta in tqdm(file_mapping.items(), desc="Semantic Chunking", unit="doc"):
            md_file_path = self.dataset_path / meta['file']
            
            if not md_file_path.exists():
                continue
                
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pre-clean Wiki Content (Remove [1], [edit], etc.)
            content = self._clean_wiki_content(content)
                
            # 1. Tách theo paragraphs (2 dòng trống trở lên)
            paragraphs = re.split(r'\n\s*\n', content)
            
            current_chunk_text = ""
            chunk_index = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para: continue
                
                # Nếu cộng thêm paragraph này vẫn < max_chars
                if len(current_chunk_text) + len(para) + 2 <= max_chars:
                    current_chunk_text += "\n\n" + para if current_chunk_text else para
                else:
                    # Đã đầy chunk -> Lưu
                    if current_chunk_text:
                        all_chunks.append(Chunk(
                            id=f"{file_hash}_sem_{chunk_index}",
                            doc_id=file_hash,
                            type='semantic_block',
                            content=current_chunk_text,
                            original_content=current_chunk_text,
                            metadata={
                                'source_url': meta['url'],
                                'doc_title': meta['title'],
                                'file_hash': file_hash,
                                'chunk_method': 'semantic_paragraph'
                            },
                            keywords=[]
                        ))
                        chunk_index += 1
                    
                    # Reset
                    if len(para) > max_chars:
                        # Paragraph is too large, split it
                        sub_chunks = Chunk.split_text_with_overlap(para, max_chars=max_chars, overlap=200)
                        
                        # Add sub-chunks as separate chunks
                        for sub_c in sub_chunks:
                            all_chunks.append(Chunk(
                                id=f"{file_hash}_sem_{chunk_index}",
                                doc_id=file_hash,
                                type='semantic_block',
                                content=sub_c,
                                original_content=sub_c,
                                metadata={
                                    'source_url': meta['url'],
                                    'doc_title': meta['title'],
                                    'file_hash': file_hash,
                                    'chunk_method': 'semantic_paragraph_split'
                                },
                                keywords=[]
                            ))
                            chunk_index += 1
                        current_chunk_text = ""
                    else:
                        current_chunk_text = para
            
            # Lưu chunk cuối cùng
            if current_chunk_text:
                all_chunks.append(Chunk(
                    id=f"{file_hash}_sem_{chunk_index}",
                    doc_id=file_hash,
                    type='semantic_block',
                    content=current_chunk_text,
                    original_content=current_chunk_text,
                    metadata={
                        **meta,
                        'chunk_method': 'semantic_paragraph'
                    },
                    keywords=[]
                ))
            
        print(f"## Semantic Chunking hoàn tất! {len(all_chunks)} chunks.")
        return all_chunks

    def _parse_single_document(self, doc_id: str, text: str, base_metadata: Dict) -> List[Chunk]:
        """Xử lý 1 file markdown cụ thể"""
        chunks = []
        
        # 1. Tách theo Chương (nếu có) hoặc xử lý toàn bộ
        chapters = self._split_chapters(text)
        
        # Danh sách entities & topics để tạo chunk tổng hợp sau này
        doc_entities = Counter()
        doc_keywords = []

        for chap_num, chap_content in chapters.items():
            # Tìm các Điều trong chương
            dieu_matches = list(re.finditer(
                r'\*\*Điều (\d+)\.\*\*\s*(.+?)(?=\*\*Điều \d+\.\*\*|\*\*Chương|\Z)',
                chap_content,
                re.DOTALL
            ))

            for match in dieu_matches:
                dieu_num = match.group(1)
                full_content = match.group(2).strip()
                
                # Tách Title và Body của Điều
                lines = full_content.split('\n', 1)
                dieu_title = lines[0].strip()
                dieu_body = lines[1] if len(lines) > 1 else ''
                
                full_dieu_title = f"Điều {dieu_num}. {dieu_title}"
                dieu_id = f"{doc_id}_dieu_{dieu_num}"
                
                # Extract NLP Keywords
                keywords = self._extract_keywords_nlp(dieu_title + " " + dieu_body)
                doc_keywords.extend(keywords)
                
                # Extract Entities
                entities = re.findall(self.patterns['org_detect'], dieu_body)
                doc_entities.update(entities)

                # --- TẠO CHUNK LEVEL 2 (ĐIỀU) ---
                # Check độ dài, nếu dài quá thì cắt nhỏ tiếp (Sliding Window)
                dieu_sub_chunks = Chunk.split_text_with_overlap(f"**{base_metadata['doc_title']}**\n{full_dieu_title}\n\n{dieu_body}")
                
                for idx, sub_content in enumerate(dieu_sub_chunks):
                    sub_id_suffix = f"_part{idx+1}" if len(dieu_sub_chunks) > 1 else ""
                    
                    dieu_chunk = Chunk(
                        id=f"{doc_id}_dieu_{dieu_num}{sub_id_suffix}",
                        doc_id=doc_id,
                        type='dieu',
                        content=sub_content,
                        original_content=f"**{full_dieu_title}**\n\n{dieu_body}" if idx == 0 else "...", # Chỉ lưu original ở part 1 để display
                        metadata={
                            **base_metadata,
                            'chuong': chap_num,
                            'dieu_so': dieu_num,
                            'level': 2,
                            'is_continuation': idx > 0
                        },
                        keywords=keywords
                    )
                    chunks.append(dieu_chunk)

                # --- TẠO CHUNK LEVEL 3 (KHOẢN) ---
                # Parse các khoản: "1. Nội dung..."
                khoan_lines = self._parse_khoans(dieu_body)
                for idx, k_content in enumerate(khoan_lines, 1):
                    # Context Injection: Ghép Title Điều vào nội dung Khoản
                    enriched_content = f"{full_dieu_title}\nKhoản {idx}. {k_content}"
                    
                    # Safety check cho Khoản (ít khi dài nhưng vẫn nên có)
                    khoan_sub_chunks = Chunk.split_text_with_overlap(enriched_content)
                    
                    for sub_idx, sub_content_k in enumerate(khoan_sub_chunks):
                         sub_id_k_suffix = f"_part{sub_idx+1}" if len(khoan_sub_chunks) > 1 else ""
                         
                         chunks.append(Chunk(
                            id=f"{dieu_id}_khoan_{idx}{sub_id_k_suffix}",
                            doc_id=doc_id,
                            type='khoan',
                            content=sub_content_k, # Context injected and split if needed
                            original_content=f"{idx}. {k_content}" if sub_idx == 0 else "...",
                            metadata={
                                **base_metadata,
                                'dieu_so': dieu_num,
                                'khoan_so': idx,
                                'parent_id': dieu_id,
                                'level': 3,
                                'is_continuation': sub_idx > 0
                            },
                            keywords=self._extract_keywords_nlp(k_content)
                        ))

        # --- TẠO CHUNK TỔNG HỢP (LEVEL 1) ---
        # 1. Summary Chunk cho toàn bộ văn bản
        top_entities = [e for e, c in doc_entities.most_common(5)]
        chunks.append(Chunk(
            id=f"{doc_id}_summary",
            doc_id=doc_id,
            type='summary',
            content=f"Tóm tắt văn bản: {base_metadata['doc_title']}\n"
                    f"Đơn vị liên quan: {', '.join(top_entities)}\n"
                    f"Nội dung chính: {', '.join(list(set(doc_keywords))[:10])}",
            original_content="Summary generated by ETL",
            metadata={**base_metadata, 'level': 1},
            keywords=list(set(doc_keywords))[:10]
        ))

        return chunks

    def _extract_keywords_nlp(self, text: str) -> List[str]:
        """
        Sử dụng Underthesea để lấy Danh từ (N) và Tên riêng (Np)
        """
        if not text:
            return []
            
        try:
            # pos_tag trả về list các tuple (word, tag)
            # Ví dụ: [('Ủy ban', 'N'), ('nhân dân', 'N'), ('Hà Nội', 'Np')]
            tags = pos_tag(text)
            
            keywords = set()
            for word, tag in tags:
                # N: Danh từ chung, Np: Danh từ riêng/Tên riêng, Ny: Từ viết tắt
                if tag in ['N', 'Np', 'Ny']: 
                    word_clean = word.strip().replace('_', ' ') # Underthesea dùng _ để nối từ ghép
                    if len(word_clean) > 2 and word_clean.lower() not in self.stopwords:
                        keywords.add(word_clean)
                        
            return list(keywords)
        except Exception as e:
            print(f"NLP Error: {e}")
            return []

    def _split_chapters(self, text: str) -> Dict[str, str]:
        """Helper tách chương"""
        chapters = {}
        matches = list(re.finditer(self.patterns['chuong'], text))
        
        if not matches:
            return {'main': text}
        
        for i, match in enumerate(matches):
            chap_num = match.group(1)
            start = match.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            chapters[chap_num] = text[start:end]
        return chapters
    
    def _parse_khoans(self, text: str) -> List[str]:
        """Helper tách khoản"""
        khoans = []
        current = []
        for line in text.split('\n'):
            line = line.strip()
            if not line: continue
            if re.match(r'^\d+\.\s+', line):
                if current: khoans.append('\n'.join(current))
                current = [re.sub(r'^\d+\.\s+', '', line)] # Remove số thứ tự ở đầu dòng text
            else:
                current.append(line)
        if current: khoans.append('\n'.join(current))
        return khoans

    def _clean_wiki_content(self, text: str) -> str:
        """
        Cleaning artifacts thường gặp trong Wiki Markdown:
        - [1], [2], [citation needed]
        - [edit], [sửa]
        - Empty links/images
        """
        if not text: return ""
        
        # 1. Remove citations like [1], [12], [nb 1]
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\[nb \d+\]', '', text)
        text = re.sub(r'\[cần dẫn nguồn\]', '', text)
        
        # 2. Remove edit links (often appear in headers like "History [edit]")
        text = re.sub(r'\[edit\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[sửa\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[sửa mã nguồn\]', '', text, flags=re.IGNORECASE)
        
        # 3. Remove artifacts like "Sửa đổi" at end of lines
        text = re.sub(r'\s+Sửa đổi\s*$', '', text, flags=re.MULTILINE)
        
        # 4. Remove empty images/links ![]() or []()
        text = re.sub(r'!\[\]\([^)]*\)', '', text)
        text = re.sub(r'\[\]\([^)]*\)', '', text)
        
        # 5. Fix multiple newlines created by removals
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def process_external_item(self, item: Dict) -> List[Chunk]:
        """
        Xử lý data từ nguồn ngoài (dạng HuggingFace Dataset row).
        
        Args:
            item: Dict chứa {'id', 'title', 'text', 'url', ...}
            
        Returns:
            List[Chunk] đã được cắt nhỏ (overlapping) và định dạng chuẩn.
        """
        chunks = []
        
        # Lấy thông tin cơ bản
        doc_id = str(item.get('id', ''))
        title = item.get('title', 'Unknown Title')
        text = item.get('text', '')
        url = item.get('url', '')
        
        # Nếu text quá ngắn hoặc rỗng
        if not text.strip():
            return []
            
        # 1. Cắt nhỏ văn bản (Sử dụng hàm split_text_with_overlap đã có)
        # Hàm này đã được cấu hình mặc định (hoặc user đã sửa) parameters.
        # Chúng ta truyền text vào.
        text_sub_chunks = Chunk.split_text_with_overlap(text)
        
        # 2. Extract keywords mẫu (trên đoạn đầu để tiết kiệm time)
        # Chỉ chạy NLP trên 1000 ký tự đầu của bài viết gốc để lấy context chung
        base_keywords = self._extract_keywords_nlp(text[:2000])

        # 3. Tạo Chunks
        for idx, sub_content in enumerate(text_sub_chunks):
            # Tạo ID duy nhất cho chunk
            chunk_id = f"{doc_id}_{idx}"
            
            # Context Injection: Đưa Title vào nội dung để Embed
            # Format: "**TITLE**\nCONTENT"
            embed_content = f"**{title}**\n{sub_content}"
            
            chunk = Chunk(
                id=chunk_id,
                doc_id=doc_id,
                type='external_article', # Loại mới
                content=embed_content,
                original_content=embed_content,
                metadata={
                    'url': url,
                    'title': title,
                    'chunk_index': idx,
                    'total_chunks': len(text_sub_chunks),
                    'source': 'external_dataset',
                    **{k:v for k,v in item.items() if k not in ['text', 'title', 'id', 'url']} # Các meta khác nếu có
                },
                keywords=base_keywords
            )
            chunks.append(chunk)
            
        return chunks

# --- MÔ PHỎNG CÁCH CHẠY (Run block) ---
if __name__ == "__main__":
    chunker = VNPTAIChunker(dataset_path="src/etl/dataset")
    result_chunks = chunker.process_dataset()
