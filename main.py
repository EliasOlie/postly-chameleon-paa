from multiprocessing import pool
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from app.schemas import PaaRequest, PaaResponse
from app.services.paa_service import process_paa

redis: Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL not set")

    pool = ConnectionPool.from_url(redis_url)
    redis = Redis(connection_pool=pool)

    await redis.execute_command("PING")

    yield

    if redis:
        await redis.close()


app = FastAPI(
    title="Postly Chameleon PAA Microservice",
    description="Gera sessões dinâmicas de People Also Ask baseadas em conteúdo.",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/generate", response_model=PaaResponse)
async def generate(request: PaaRequest):
    try:
        html, ld = await process_paa(request.content, request.include_sponsored)
        
        return PaaResponse(
            html_fragment=html,
            json_ld=ld
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Postly Chameleon PAA"}