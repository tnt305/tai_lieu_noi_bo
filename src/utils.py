import yaml
import os
import time
from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Determine project root (parent directory of 'src')
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")

# Load .env file if present
load_dotenv(env_path)

from src.crawler.domain_cfg import THU_VIEN_PHAP_LUAT_CFG_MAPPING

def load_llm_config(model_type: str):
    config_path = os.getenv("LLM_CONFIG_PATH")
    if not config_path:
        # Fallback to default config path relative to project_root
        config_path = os.path.join(project_root, "src", "rag", "config", "llm.yaml")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Environment variable overrides for security and flexibility
    prefix_map = {
        "small": "LLM_SMALL",
        "large": "LLM_LARGE",
        "embeddings": "LLM_EMBED"
    }
    
    field_map = {
        "authorization": "AUTH",
        "tokenId": "TOKEN_ID",
        "tokenKey": "TOKEN_KEY",
        "llmApiName": "API_NAME"
    }
    
    if model_type in prefix_map:
        prefix = prefix_map[model_type]
        for config_key, env_suffix in field_map.items():
            env_var = f"{prefix}_{env_suffix}"
            env_val = os.getenv(env_var)
            if env_val:
                if config_key in config['models'][model_type]:
                    config['models'][model_type][config_key] = env_val
            
    return config['models'][model_type]

def load_tvpl_url(domain: str = None, mode='individual'):
    """
    Load url từ Thư viện pháp luật
    """
    BASE_URL = "https://thuvienphapluat.vn/van-ban-moi"

    if mode=="individual":
        if domain not in THU_VIEN_PHAP_LUAT_CFG_MAPPING:
            raise ValueError(f"Domain {domain} not found in THU_VIEN_PHAP_LUAT_CFG_MAPPING")
        return BASE_URL, f"{BASE_URL}/{domain}?ft=1"
    if mode == "full":
        urls = []
        for k in THU_VIEN_PHAP_LUAT_CFG_MAPPING.keys():
            urls.append(f"{BASE_URL}/{k}?ft=1")
        return BASE_URL, urls
    raise ValueError("Mode must be 'individual' or 'full'")

def crawl_with_selenium(url, wait_time=5):
    """
    Crawl website với Selenium để bypass Cloudflare
    
    Args:
        url: URL cần crawl
        wait_time: Thời gian chờ Cloudflare (giây), mặc định 5s
    
    Returns:
        BeautifulSoup object chứa HTML đã được render
    
    Example:
        >>> soup = crawl_with_selenium("https://example.com")
        >>> div = soup.find("div", id="content")
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    
    # Đường dẫn tới chromedriver local (trong thư mục project)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chromedriver_path = os.path.join(project_root, "chromedriver-linux64", "chromedriver")
    
    if not os.path.exists(chromedriver_path):
        raise FileNotFoundError(
            f"Chromedriver not found at {chromedriver_path}\n"
            "Please download it from: https://googlechromelabs.github.io/chrome-for-testing/"
        )
    
    # Cấu hình Chrome options
    options = Options()
    options.add_argument("--headless")  # Chạy ẩn
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Ẩn automation
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    
    # Khởi tạo Service với chromedriver local
    service = Service(executable_path=chromedriver_path)
    
    # Khởi tạo driver
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        print(f"🌐 Đang truy cập: {url}")
        driver.get(url)
        
        # Chờ Cloudflare load xong (có thể điều chỉnh thời gian)
        print(f"⏳ Đang chờ Cloudflare ({wait_time}s)...")
        time.sleep(wait_time)
        
        # Lấy HTML sau khi Cloudflare đã xử lý
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        print("✅ Đã lấy được HTML thành công!")
        return soup
        
    finally:
        driver.quit()