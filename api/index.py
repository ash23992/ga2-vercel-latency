from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import statistics
from typing import List

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: float

@app.post("/api/latency")
async def latency(data: RequestBody):
    # Load telemetry data
    with open("q-vercel-latency.json") as f:
        records = json.load(f)

    response = {}

    for region in data.regions:
        region_records = [r for r in records if r["region"] == region]

        if not region_records:
            continue

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime"] for r in region_records]

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95) - 1]
        avg_uptime = statistics.mean(uptimes)
        breaches = sum(1 for l in latencies if l > data.threshold_ms)

        response[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return response
