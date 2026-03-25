# load_balancer_v2.py

import asyncio
import random
import time
import httpx
from collections import Counter

# List of backend server endpoints to balance traffic across
SERVERS = [
    "http://127.0.0.1:5001/ping",
    "http://127.0.0.1:5002/ping",
    "http://127.0.0.1:5003/ping",
    "http://127.0.0.1:5004/ping",
    "http://127.0.0.1:5005/ping",
]

# Stores latency estimates for each server (None at startup)
latency_estimates = {url: None for url in SERVERS}

# Smoothing factor for Exponential Moving Average (EMA)
ALPHA = 0.3


async def send_request(client: httpx.AsyncClient, url: str):
    """
    Sends a request to the given server and measures how long it takes.
    Updates the latency estimate for that server using EMA.
    Returns the server URL, measured latency, and response data.
    """
    start = time.time()
    try:
        resp = await client.get(url, timeout=10.0)
        elapsed = (time.time() - start) * 1000  # ms
        data = resp.json()
    except Exception as e:
        # If the request fails, treat it as very slow
        elapsed = 9999
        data = {"error": str(e)}

    # Update the latency estimate using EMA
    old = latency_estimates[url]
    if old is None:
        latency_estimates[url] = elapsed
    else:
        latency_estimates[url] = ALPHA * elapsed + (1 - ALPHA) * old

    return url, elapsed, data


def pick_server():
    """
    Chooses which server to send a request to:
    - 95% of the time, pick the fastest known server ("exploit").
    - 5% of the time, pick a different server to explore.
    - If no latency data yet, pick randomly.
    """
    known = {k: v for k, v in latency_estimates.items() if v is not None}
    if not known:
        return random.choice(SERVERS)

    best_server = min(known, key=known.get)

    if random.random() < 0.95:
        return best_server
    else:
        others = [s for s in SERVERS if s != best_server]
        return random.choice(others)


async def traffic_generator():
    """
    Main loop that simulates client traffic:
    - Every round, sends 100 requests to servers.
    - Picks servers using the explore/exploit strategy.
    - Prints a summary of latency and traffic distribution after each round.
    - Waits 20 seconds before starting the next round.
    """
    async with httpx.AsyncClient() as client:
        round_num = 1
        while True:
            tasks = []
            chosen_servers = []
            for _ in range(100):
                server = pick_server()
                chosen_servers.append(server)
                tasks.append(send_request(client, server))

            await asyncio.gather(*tasks)

            # Count how many requests went to each server
            counts = Counter(chosen_servers)

            # Print summary for this round
            print(f"\n=== Traffic Round {round_num} Summary ===")
            for url in SERVERS:
                est = latency_estimates[url]
                count = counts.get(url, 0)
                if est:
                    print(f"{url}: avg={est:.2f} ms, requests={count}")
                else:
                    print(f"{url}: no data yet, requests={count}")

            round_num += 1

            # Wait before next round
            await asyncio.sleep(20)


if __name__ == "__main__":
    # Start the traffic simulation when running this script
    asyncio.run(traffic_generator())
