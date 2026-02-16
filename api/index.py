from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import statistics
from typing import List

app = FastAPI()

# ✅ Proper CORS for Vercel (must allow OPTIONS too)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: float


@app.post("/latency")
async def latency(data: RequestBody):

    # ✅ Safe file loading on Vercel
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "../q-vercel-latency.json")

    with open(file_path) as f:
        records = json.load(f)

    response = {}

    for region in data.regions:
        region_records = [r for r in records if r["region"] == region]

        if not region_records:
            continue

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime"] for r in region_records]

        avg_latency = statistics.mean(latencies)

        # Proper p95 calculation
        sorted_lat = sorted(latencies)
        index = int(0.95 * len(sorted_lat)) - 1
        p95_latency = sorted_lat[max(index, 0)]

        avg_uptime = statistics.mean(uptimes)

        breaches = sum(1 for l in latencies if l > data.threshold_ms)

        response[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return response
