from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Dict
from uuid import uuid4
from agent.models import AnalysisRequest, AnalysisStatus
from agent.orchestrator import MarketAnalysisOrchestrator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="E-commerce Market Analysis Agent API",
    description="API to generate automated and personalized market analyses based on real-time data."
)

# In-memory storage for tasks. In production, use Redis or a Database.
tasks_db: Dict[str, AnalysisStatus] = {}

# We initialize the orchestrator
orchestrator = MarketAnalysisOrchestrator()

@app.post("/api/v1/analyze", response_model=AnalysisStatus, status_code=202)
async def submit_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    
    tasks_db[task_id] = AnalysisStatus(
        task_id=task_id,
        status="running"
    )
    
    background_tasks.add_task(run_agent_task, task_id, request)
    return tasks_db[task_id]

@app.get("/api/v1/analyze/{task_id}", response_model=AnalysisStatus)
async def get_analysis_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

async def run_agent_task(task_id: str, request: AnalysisRequest):
    try:
        response = await orchestrator.run_analysis(
            product_name=request.product_name,
            competitors=request.competitors,
            market_segment=request.market_segment
        )
        tasks_db[task_id].status = "completed"
        tasks_db[task_id].result = response.model_dump()
    except Exception as e:
        tasks_db[task_id].status = "failed"
        tasks_db[task_id].error = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
