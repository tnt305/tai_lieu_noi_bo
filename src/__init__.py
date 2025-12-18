# Lazy imports to avoid loading heavy dependencies (bs4, selenium) at package init
def load_llm_config(model_type: str):
    from .utils import load_llm_config as _load_llm_config
    return _load_llm_config(model_type)

def load_tvpl_url(domain: str = None, mode='individual'):
    from .utils import load_tvpl_url as _load_tvpl_url
    return _load_tvpl_url(domain, mode)

def crawl_with_selenium(url, wait_time=5):
    from .utils import crawl_with_selenium as _crawl_with_selenium
    return _crawl_with_selenium(url, wait_time)

__all__ = ["load_llm_config", "load_tvpl_url", "crawl_with_selenium"]