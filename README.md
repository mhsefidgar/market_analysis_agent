# Market Analysis Agent

A production-oriented e-commerce market analysis agent built with **FastAPI, Pydantic, and native LLM tool calling**. The system accepts an analysis request, orchestrates specialized tools, records an execution trace, and returns a structured market report.

## Why this project?

This project demonstrates AI-engineering patterns beyond a prompt demo:

- Native tool-calling orchestration with explicit control flow
- Pydantic validation for tool arguments and API contracts
- Bounded agent execution to prevent infinite loops
- Resilient tool failures fed back into the model as structured errors
- Async API with `202 Accepted` task lifecycle
- Per-tool execution tracing and latency measurement
- Health endpoint and typed API responses
- Docker-ready deployment
- Automated tests

> **Important:** The current bundled tools are deterministic demo adapters that simulate external data sources. They are intentionally isolated behind the `Tool` interface so real pricing, reviews, news, or market-data providers can be added without changing the orchestrator.

## Architecture

```text
Client
  |
  v
FastAPI /api/v1/analyze
  |
  +--> 202 + task_id
  |
  v
MarketAnalysisOrchestrator
  |
  +--> LLM tool selection
  |       |
  |       +--> WebScraperTool
  |       +--> SentimentAnalyzerTool
  |       +--> MarketTrendAnalyzerTool
  |       +--> ReportGeneratorTool
  |
  +--> validation + error recovery
  +--> execution trace / latency
  |
  v
AgentResponse
  |
  +--> report
  +--> tool_calls_made
  +--> execution_trace
```

## API

### Submit an analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Sony WH-1000XM5",
    "competitors": ["Bose QuietComfort Ultra", "AirPods Max"],
    "market_segment": "Premium wireless headphones"
  }'
```

The endpoint returns `202 Accepted` with a `task_id`.

### Poll the result

```bash
curl http://localhost:8000/api/v1/analyze/<task_id>
```

### Health check

```bash
curl http://localhost:8000/health
```

Interactive API documentation is available at `/docs`.

## Example response shape

```json
{
  "task_id": "...",
  "status": "completed",
  "result": {
    "report": "...",
    "tool_calls_made": 4,
    "execution_trace": [
      {
        "tool_name": "web_scraper",
        "status": "success",
        "duration_ms": 501.2
      }
    ]
  }
}
```

## Engineering decisions

### Native orchestration instead of a heavy agent framework

The orchestration loop is intentionally implemented directly against the OpenAI-compatible tool-calling API. This keeps tool dispatch, validation, failure handling, and iteration limits visible and testable.

### Bounded execution

Every request has a configurable maximum number of agent iterations. This prevents accidental infinite tool loops and gives a clear failure mode when the model cannot finish an analysis.

### Tool isolation

Each capability implements the same `Tool` interface and exposes a Pydantic argument schema. A production implementation can replace the demo scraper with a marketplace API, replace the sentiment adapter with a review pipeline, or add financial/news tools without rewriting the orchestrator.

### Observability

Each tool call records:

- tool name
- success/failure status
- execution latency
- error information when applicable

The next production step is exporting this trace to OpenTelemetry/Langfuse and recording token usage, model latency, cost, and end-to-end task duration.

## Production roadmap

1. Replace simulated tools with real provider adapters.
2. Persist tasks and results in PostgreSQL/Redis instead of process memory.
3. Move long-running work to a durable queue such as Celery/RQ/Redis Streams.
4. Add retrieval and source citation support for every market claim.
5. Add an evaluation dataset with retrieval, tool-selection, factuality, latency, and cost metrics.
6. Add OpenTelemetry/Langfuse tracing and Prometheus metrics.
7. Add authentication, rate limiting, retries, circuit breakers, and provider timeouts.
8. Add CI/CD and deploy the API as a containerized service.

## Local development

Requirements: Python 3.13+, Git

```bash
git clone https://github.com/mhsefidgar/market_analysis_agent.git
cd market_analysis_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Create `.env`:

```env
OPENAI_API_KEY=your-api-key
MODEL_NAME=gpt-4o-mini
# Optional OpenAI-compatible endpoint:
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

Run:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```

## Project structure

```text
market_analysis_agent/
├── agent/
│   ├── models.py          # API/domain models
│   ├── orchestrator.py    # LLM + tool-calling loop
│   └── tools.py           # Tool interface and adapters
├── tests/
│   ├── test_agent.py
│   └── test_tools.py
├── main.py                # FastAPI application
├── requirements.txt
├── Dockerfile
└── README.md
```

## Status

The repository is a reference implementation for an AI-engineering portfolio project. The orchestration, API contracts, validation, bounded execution, and tracing are production-oriented; external market-data integrations and durable infrastructure remain roadmap items.
