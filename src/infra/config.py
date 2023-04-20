from functools import lru_cache

from pydantic import BaseSettings


# BaseSettings automatically bind os.environ with lowercase()
class Cfg(BaseSettings):
    phase: str
    redis_uri: str
    openai_api_key: str
    openai_model: str
    max_crawl_page: int
    max_text_limit: int
    redis_host: str
    redis_password: str
    


@lru_cache()
def get_config():
    return Cfg()
