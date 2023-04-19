from functools import lru_cache

from pydantic import BaseSettings


# BaseSettings automatically bind os.environ with lowercase()
class Cfg(BaseSettings):
    # The default URL expects the app to run using Docker and docker-compose.
    phase: str
    redis_uri: str
    openai_api_key: str


@lru_cache()
def get_config():
    return Cfg()
