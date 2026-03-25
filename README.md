# Adaptive Load Balancer Simulation

> Built from scratch to understand how real load balancers think — not just round-robin, but adaptive routing that learns which servers are fast and keeps checking if that's still true.

A client-side load balancer simulation in Python that routes traffic intelligently based on real-time server latency. Uses an **ε-greedy explore/exploit strategy** (borrowed from reinforcement learning) and **Exponential Moving Average (EMA)** to continuously learn and adapt to changing server conditions — without any external libraries or frameworks beyond FastAPI and httpx.

**Skills demonstrated:** async Python, distributed systems concepts, algorithmic decision-making, system simulation

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Load Balancer (load_balancer_v2.py)            │
│                                                                  │
│  Every 20 seconds:                                               │
│  ─ Fires 100 concurrent async requests                          │
│  ─ pick_server() selects a target for each request              │
│  ─ Measures round-trip latency, updates per-server EMA          │
│  ─ Prints a traffic distribution + latency summary              │
└────────────────┬───────────────────────────────┬────────────────┘
                 │ 95% exploit                   │ 5% explore
                 ▼                               ▼
     ┌──────── :5001 ──────┐        ┌──── :5002 / :5003 / :5004 / :5005 ────┐
     │  fastest known      │        │  random non-best server                │
     └─────────────────────┘        └────────────────────────────────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                  5 FastAPI servers (server.py)
                  Each /ping sleeps for latency_ms, then responds.
                  Latency updates every 60 s:
                    80% — small jitter  (±20 ms)
                    20% — new random value (50–2000 ms)
```

### Exponential Moving Average (EMA)

Each server's latency is tracked with EMA to smooth out noise:

```
new_estimate = α × measured + (1 − α) × old_estimate
```

- `α = 0.3` — 30% weight on the latest measurement, 70% on history
- Smooths spikes without ignoring trends
- No need to store historical data points

### Explore / Exploit Strategy

```
95% of requests → fastest server by EMA  (exploit)
 5% of requests → random other server    (explore)
```

This is a simplified **ε-greedy** policy from multi-armed bandit theory:
- **Exploit** sends traffic to the known best server for efficiency.
- **Explore** keeps probing others so the balancer can detect when a previously slow server improves.
- Without exploration, a server that recovers from high latency would never receive traffic again.

---

## Project Structure

```
Load_balancing/
├── server.py             # Simulated FastAPI backend with dynamic latency
├── load_balancer_v2.py   # Async load balancer with EMA + explore/exploit
└── requirements.txt      # Python dependencies
```

---

## Getting Started

### 1. Install Dependencies

```sh
pip install -r requirements.txt
```

Or install the core packages directly:

```sh
pip install fastapi "uvicorn[standard]" httpx
```

### 2. Start the Backend Servers

Open **five separate terminals** and run one command in each:

```sh
uvicorn server:app --port 5001
uvicorn server:app --port 5002
uvicorn server:app --port 5003
uvicorn server:app --port 5004
uvicorn server:app --port 5005
```

Each server instance starts with a random latency between 50 ms and 2000 ms, which then drifts over time.

### 3. Run the Load Balancer

```sh
python load_balancer_v2.py
```

### Sample Output

```
=== Traffic Round 1 Summary ===
http://127.0.0.1:5001/ping: avg=112.34 ms, requests=4
http://127.0.0.1:5002/ping: avg=843.21 ms, requests=3
http://127.0.0.1:5003/ping: avg=67.89 ms, requests=88
http://127.0.0.1:5004/ping: avg=310.45 ms, requests=3
http://127.0.0.1:5005/ping: avg=1204.77 ms, requests=2

=== Traffic Round 2 Summary ===
http://127.0.0.1:5001/ping: avg=109.02 ms, requests=5
http://127.0.0.1:5002/ping: avg=820.44 ms, requests=2
http://127.0.0.1:5003/ping: avg=65.11 ms, requests=91
...
```

Traffic concentrates on the fastest server while a small fraction continuously probes the others.

---

## Configuration

All tunable parameters live in `load_balancer_v2.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SERVERS` | 5 URLs on ports 5001–5005 | Backend server endpoints |
| `ALPHA` | `0.3` | EMA smoothing factor. Higher → reacts faster to changes |
| Requests per round | `100` | Number of concurrent requests sent each round |
| Round interval | `20 s` | Pause between traffic rounds (`asyncio.sleep`) |

Server behavior is controlled in `server.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Initial latency | 50–2000 ms | Random on each server startup |
| Update interval | `60 s` | How often latency changes |
| Jitter (80% of updates) | ±20 ms | Small drift, simulates normal variance |
| Reset (20% of updates) | 50–2000 ms | Large jump, simulates network events |
| Minimum latency | `10 ms` | Floor applied after jitter |

---

## Key Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Exponential Moving Average | `send_request()` in `load_balancer_v2.py` |
| ε-greedy explore/exploit | `pick_server()` in `load_balancer_v2.py` |
| Async concurrent requests | `asyncio.gather()` in `traffic_generator()` |
| Dynamic server simulation | `update_latency_task()` in `server.py` |
| FastAPI lifespan events | `lifespan()` context manager in `server.py` |
