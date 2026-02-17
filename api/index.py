from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import statistics
import os
import math

app = FastAPI()

# CORS configuration (Vercel + grader safe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: float

# Explicit OPTIONS handler for preflight
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/")
async def latency(data: RequestBody):
    file_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "q-vercel-latency.json"
    )

    with open(file_path) as f:
        records = json.load(f)

    region_results = {}

    for region in data.regions:
        region_records = [r for r in records if r["region"] == region]

        if not region_records:
            continue

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]

        avg_latency = round(statistics.mean(latencies), 2)
        avg_uptime = round(statistics.mean(uptimes), 3)
        breaches = sum(1 for l in latencies if l > data.threshold_ms)

        # NumPy-style 95th percentile (linear interpolation)
        sorted_latencies = sorted(latencies)
        k = (len(sorted_latencies) - 1) * 0.95
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            p95_latency = sorted_latencies[int(k)]
        else:
            d0 = sorted_latencies[int(f)] * (c - k)
            d1 = sorted_latencies[int(c)] * (k - f)
            p95_latency = d0 + d1

        p95_latency = round(p95_latency, 2)

        region_results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return {"regions": region_results}
