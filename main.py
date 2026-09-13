from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException

from agent.models import AnalysisRequest, AnalysisStatus, TaskStatus
from agent.orchestrator import MarketAnalysisOrchestrator

load_dotenv()

app = FastAPI(
    title="E-commerce Market Analysis Agent API",
    version="2.0.0",
    description="Asynchronous, tool-calling market analysis with execution tracing.",
)

tasks_db: Dict[str, AnalysisStatus] = {}
orchestrator = MarketAnalysisOrchestrator()


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalysisStatus, status_code=202, tags=["analysis"])
async def submit_analysis(
    request: AnalysisRequest, background_tasks: BackgroundTasks
) -> AnalysisStatus:
    task_id = str(uuid4())
    tasks_db[task_id] = AnalysisStatus(task_id=task_id, status=TaskStatus.QUEUED)
    background_tasks.add_task(run_agent_task, task_id, request)
    return tasks_db[task_id]


@app.get("/api/v1/analyze/{task_id}", response_model=AnalysisStatus, tags=["analysis"])
async def get_analysis_status(task_id: str) -> AnalysisStatus:
    task = tasks_db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def run_agent_task(task_id: str, request: AnalysisRequest) -> None:
    task = tasks_db[task_id]
    task.status = TaskStatus.RUNNING
    try:
        task.result = await orchestrator.run_analysis(
            product_name=request.product_name,
            competitors=request.competitors,
            market_segment=request.market_segment,
        )
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error = f"{type(exc).__name__}: {exc}"
        task.completed_at = datetime.now(timezone.utc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
