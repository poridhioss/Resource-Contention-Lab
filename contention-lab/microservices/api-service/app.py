import time
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import math
import psutil
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Latency-Sensitive API", version="1.0.0")

class WorkRequest(BaseModel):
    delay_ms: int = 20
    complexity: str = "low"  # low, medium, high

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    pid: int
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float

start_time = time.time()

def cpu_bound_work(ms: int, complexity: str = "low") -> float:
    """
    Simulate CPU-bound work for specified milliseconds
    """
    end_time = time.perf_counter() + (ms / 1000.0)
    result = 0.0
    
    # Adjust computation intensity based on complexity
    multiplier = {"low": 1, "medium": 3, "high": 10}.get(complexity, 1)
    
    iteration_count = 0
    while time.perf_counter() < end_time:
        for _ in range(100 * multiplier):
            result += math.sqrt(12345.6789) * math.sin(iteration_count)
            result += math.cos(iteration_count) * math.log(iteration_count + 1)
            iteration_count += 1
    
    return result

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint with system metrics"""
    try:
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        uptime = time.time() - start_time
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            pid=os.getpid(),
            cpu_percent=cpu_percent,
            memory_mb=round(memory_mb, 2),
            uptime_seconds=round(uptime, 2)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/work")
async def work(request: WorkRequest):
    """
    Perform CPU-bound work - this endpoint will show degradation under contention
    """
    start = time.perf_counter()
    
    try:
        # Log the request
        logger.info(f"Processing work request: {request.delay_ms}ms, complexity: {request.complexity}")
        
        # Perform CPU-bound work
        result = cpu_bound_work(request.delay_ms, request.complexity)
        
        actual_time_ms = (time.perf_counter() - start) * 1000
        
        # Log if we're significantly slower than expected
        if actual_time_ms > request.delay_ms * 2:
            logger.warning(f"Slow processing detected: expected ~{request.delay_ms}ms, actual {actual_time_ms:.2f}ms")
        
        return {
            "status": "completed",
            "requested_delay_ms": request.delay_ms,
            "actual_time_ms": round(actual_time_ms, 2),
            "complexity": request.complexity,
            "result_hash": hash(str(result)) % 10000,  # Simple hash for verification
            "pid": os.getpid(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Work processing failed: {e}")
        raise HTTPException(status_code=500, detail="Work processing failed")

@app.get("/work")  # GET version for easier testing
async def work_get(delay_ms: int = 20, complexity: str = "low"):
    """GET version of work endpoint for easier curl testing"""
    request = WorkRequest(delay_ms=delay_ms, complexity=complexity)
    return await work(request)

@app.get("/stress")
async def stress_test(duration_seconds: int = 10, intensity: str = "medium"):
    """
    Stress test endpoint to generate sustained load
    """
    if duration_seconds > 60:
        raise HTTPException(status_code=400, detail="Duration cannot exceed 60 seconds")
    
    start_time = time.perf_counter()
    results = []
    
    while (time.perf_counter() - start_time) < duration_seconds:
        result = cpu_bound_work(50, intensity)  # 50ms chunks
        results.append(hash(str(result)) % 1000)
        await asyncio.sleep(0.01)  # Small yield
    
    actual_duration = time.perf_counter() - start_time
    
    return {
        "status": "completed",
        "requested_duration": duration_seconds,
        "actual_duration": round(actual_duration, 2),
        "iterations": len(results),
        "intensity": intensity,
        "pid": os.getpid()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")