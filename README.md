# E-commerce Market Analysis Agent

An intelligent agent designed to orchestrate multiple tools and produce comprehensive strategic reports on specific products or markets.

## Architecture & Implementation Choices

### Native Approach vs. Frameworks
This project relies on a **Native Framework approach** built directly in Python utilizing `FastAPI`, `Pydantic`, and the `OpenAI API SDK` (which natively supports function calling).

**Justification:**
1. **Clarity over Complexity:** Many popular agent frameworks (LangGraph, CrewAI) introduce heavy abstractions and black-box components that can complicate debugging and restrict custom logic.
2. **Standardization:** Using the OpenAI function calling schema as the interface allows seamless swapping of underlying models (OpenAI, DeepSeek, Anthropic, OpenRouter) with minimal adjustments.
3. **Ease of Maintenance:** The orchestrator loop explicitly handles tool dispatch and result injection, allowing developers to see exactly how and when external calls are made.

---

## Advanced Architecture & Features

This project implements several production-grade patterns designed to fulfill the **Advanced Features** and **LLM Integration** criteria:

- **Native ReAct Orchestration**: A custom-built Reasoning and Acting loop (`agent/orchestrator.py`) allowing the agent to dynamically react to tool outputs and "self-correct" if a tool returns an error.
- **Automatic Tool Schema Mapping**: Utilizes Pydantic's metadata to automatically generate OpenAI-compliant JSON schemas for tool arguments. This significantly improves **DX (Developer Experience)** by enabling "plug-and-play" tool registration.
- **Asynchronous Task Architecture**: Implements a `202 Accepted` pattern for long-running LLM analyses. Analysis requests are processed as **FastAPI Background Tasks**, preventing timeouts and decoupling the request/response lifecycle.
- **Resilient Tool Dispatch**: Every tool execution is wrapped in a fail-safe block. Errors are caught and fed back into the LLM context, enabling the agent to handle tool failures (e.g., a blocked scraper) gracefully rather than crashing.

---

## Installation & Usage

### 1. Local Setup

**Requirements:** Python 3.13+, Git

1. Clone the repository:
```bash
git clone <your-repo-link>
cd market_analysis_agent
```
2. Set up the virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Set Environment Variables:
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your-api-key-here
# Optional overriding for other providers:
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
# MODEL_NAME=anthropic/claude-3-haiku
```

### 2. Running the API

Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000/docs` to interact with the Swagger API interface.

### 3. Docker Containerization

To deploy using Docker:
```bash
docker-compose up --build -d
```
The API will be available at `http://localhost:8000`.

---

## Theoretical Questionnaire

### 1. Data Architecture and Storage
**Schema Design**:
- `AnalysisRequest`: Original request data.
- `ToolExecutionHistory`: Logs of which tools were called, inputs, and outputs.
- `AnalysisResult`: Final compiled insights.

**Recommended System**:
- **PostgreSQL**: For persistent storage of users, request history, and analysis records. It natively supports JSONB schemas which is ideal for storing dynamic tool execution histories and AI outputs.
- **Redis (Cache layer)**: To store recently queried raw data (e.g., product pricing and sentiment metrics). Instead of hitting web scrapers multiple times for the same product in a short window, Redis provides fast intermediate lookups.

### 2. Monitoring and Observability
- **Execution Tracing (Tracing):** Integrate **OpenTelemetry** or **Langfuse**. This allows us to trace the complete chain: API invocation -> Orchestrator loops -> Tool executions -> LLM responses.
- **Performance Metrics:** Using **Prometheus** + **Grafana** to monitor response times, error rates (e.g., failed scraping), and LLM latency.
- **Alerting:** Set up trigger-based alerts in **PagerDuty** or Slack for high failure rates (e.g., API limits reached or 500 status codes).
- **Key Metrics to Monitor:** Number of tool calls per request (prevents loops), LLM token usage, analysis duration, and tool success rate.

### 3. Scaling and Optimization
- **Load Peaks (100+ simultaneous queries):** Use Celery or RabbitMQ to build an async task queue. The FastAPI endpoints already return `202 Accepted` returning a `task_id`. Background workers can process analyses safely scaling horizontally decoupled from incoming traffic.
- **Optimizing LLM Costs:** Use prompt caching (supported by Anthropic & OpenAI) to reuse instructions. Route simple reasoning (like deciding which tools to call) to cheaper/faster models (e.g., GPT-4o-mini or Claude Haiku) and reserve complex reasoning (report generation) for heavier models.
- **Intelligent Caching:** Cache tool outputs. If a "Sentiment Tool" was run for "iPhone 15" within the last 24hrs, return the cached result instead of re-processing.
- **Parallelization:** Tools that do not depend on each other (e.g. `web_scraper` and `sentiment_analyzer`) can be executed concurrently using `asyncio.gather`. 

### 4. Continuous Improvement and A/B Testing
- **LLM as a Judge:** Periodically sample generated reports and pass them to an independent LLM (e.g., GPT-4) armed with a rubric evaluating formatting, data accuracy, and insightfulness.
- **A/B Testing Prompts:** Use an experiment tracking tool like **LangSmith**. Direct 50% of the traffic to the V1 system prompt and 50% to V2. Evaluate which variant takes fewer tool calls (latency) or scores higher on the LLM judge proxy.
- **Feedback Loop:** Expose a `POST /analyze/{task_id}/feedback` endpoint for end-users to provide a thumbs up/down and text feedback. Store this for fine-tuning.
- **Evolving Capabilities:** Incrementally add new tools to the `ToolRegistry` (e.g., RedditScraper, CompetitorPricingAPI). The agent natively scales its capabilities just by exposing the new tools via the function call schema.
