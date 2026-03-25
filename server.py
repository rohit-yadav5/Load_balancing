# server.py

import random
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Initialize a global latency variable (in milliseconds).
# This simulates how "slow" or "fast" the server responds.
latency_ms = random.randint(50, 2000)


async def update_latency_task():
    """
    Background task that periodically updates the server's latency.
    - Every 1 minute, latency may change.
    - 80% chance: latency changes slightly (simulates jitter).
    - 20% chance: latency jumps to a new random value (simulates network events).
    """
    global latency_ms
    while True:
        await asyncio.sleep(60)  # Wait 1 minute before updating latency.
        if random.random() < 0.8:  # Most of the time, make a small change.
            jitter = random.randint(-20, 20)
            latency_ms = max(10, latency_ms + jitter)
        else:  # Occasionally, make a big change.
            latency_ms = random.randint(50, 2000)
        print(f"⚡ Latency updated to {latency_ms} ms")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Launch the background latency updater when the server starts."""
    asyncio.create_task(update_latency_task())
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/ping")
async def ping():
    """
    Simulates a server response:
    - Waits for the current latency (in ms).
    - Returns a JSON with status and current latency.
    """
    await asyncio.sleep(latency_ms / 1000)  # Convert ms to seconds for asyncio.sleep
    return {"status": "ok", "latency_ms": latency_ms}
