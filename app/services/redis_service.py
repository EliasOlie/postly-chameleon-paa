# app/services/redis_service.py
import json
import hashlib
import redis.asyncio as redis
import os
from functools import wraps

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

def cache_paa(expire: int = 86400): # 24 horas de cache default
    """
    Decorator elegante para cachear o resultado da função generate_paa.
    A chave será um Hash do conteúdo do post.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(content: str, include_sponsored: bool, *args, **kwargs):
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            sponsor_flag = "1" if include_sponsored else "0"
            cache_key = f"paa:{content_hash}:{sponsor_flag}"

            cached_data = await redis_client.get(cache_key)
            if cached_data:
                print(f"⚡ Cache Hit: {cache_key}")
                return json.loads(cached_data)

            print(f"🐢 Cache Miss (Gerando IA): {cache_key}")
            result = await func(content, include_sponsored, *args, **kwargs)

            await redis_client.set(cache_key, json.dumps(result), ex=expire)
            
            return result
        return wrapper
    return decorator