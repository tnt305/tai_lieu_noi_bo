import json
import hashlib
import os
import trafilatura
from pathlib import Path
from tqdm import tqdm

def get_file_hash(url):
    return hashlib.md5(url.encode()).hexdigest()[:16]

def convert_jsonl_to_dataset(jsonl_paths, output_dir="src/etl/dataset"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    mapping_file = output_path / "file_mapping.json"
    existing_mapping = {}
    
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            try:
                existing_mapping = json.load(f)
            except:
                pass

    new_mapping = existing_mapping.copy()
    
    for jsonl_path in jsonl_paths:
        if not os.path.exists(jsonl_path):
            print(f"Skipping {jsonl_path}, file not found.")
            continue
            
        print(f"Processing {jsonl_path}...")
        
        # Load all lines first to get total count for tqdm
        data_items = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data_items.append(json.loads(line))
                    except:
                        pass
        
        for item in tqdm(data_items, desc=f"Converting {os.path.basename(jsonl_path)}"):
            try:
                url = item.get('url')
                # content in jsonl might be just a title or short snippet
                # user wants to fetch full markdown content using trafilatura if not present or to ensure tables are included
                
                if not url:
                    continue

                # Try to fetch fresh content with tables
                try:
                    downloaded = trafilatura.fetch_url(url)
                    if downloaded:
                        markdown = trafilatura.extract(
                            downloaded,
                            output_format="markdown",
                            include_tables=True, # Requested change
                            include_images=False
                        )
                        if markdown is None:
                             markdown = item.get('markdown', '') or item.get('content', '')
                    else:
                        markdown = item.get('markdown', '') or item.get('content', '')
                except Exception as err:
                    print(f"Failed to fetch {url}: {err}")
                    markdown = item.get('markdown', '') or item.get('content', '')

                file_hash = get_file_hash(url)
                file_name = f"{file_hash}.md"
                
                if not markdown:
                    continue
                    
                # Save MD file
                with open(output_path / file_name, 'w', encoding='utf-8') as md_file:
                    md_file.write(markdown)
                    
                # Update mapping
                new_mapping[file_hash] = {
                    "title": item.get('content', 'No Title')[:200], # Use original content field as title if available
                    "url": url,
                    "file": file_name
                }
                
            except Exception as e:
                print(f"Error processing line: {e}")
                continue

    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(new_mapping, f, ensure_ascii=False, indent=2)
        
    print(f"Conversion complete. Mapping saved to {mapping_file}")

if __name__ == "__main__":
    # Add your jsonl files here
    # jsonl_files = [
    #     # "src/crawler/nghidinh.jsonl",
    #     # "src/crawler/viwiki_2025.jsonl",
    #     "src/crawler/fullthuvienphapluat.jsonl",
    #     "src/crawler/wwiki_chinhtri.jsonl",
    # ]
    import os
    jsonl_files = ["src/crawler/" + i for i in  os.listdir("src/crawler/") if i.endswith(".jsonl")]
    convert_jsonl_to_dataset(jsonl_files)
