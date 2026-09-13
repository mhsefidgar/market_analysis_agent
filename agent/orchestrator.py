import json
import os
import time
from typing import Any, List, Optional

from openai import AsyncOpenAI

from .models import AgentResponse, ToolExecution
from .tools import ToolRegistry, get_default_registry


class MarketAnalysisOrchestrator:
    """Tool-calling agent with bounded execution and observable tool traces."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        registry: Optional[ToolRegistry] = None,
        max_iterations: int = 8,
    ):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        self.model = os.getenv("MODEL_NAME", model)
        self.registry = registry or get_default_registry()
        self.max_iterations = max_iterations
        self.system_prompt = """
You are an expert e-commerce market analysis agent.

Produce evidence-based strategic analysis. Use tools for every factual claim that
requires external or computed data. Never invent prices, ratings, trends, reviews,
or competitor facts. If a tool fails, acknowledge the missing evidence instead of
fabricating a replacement.

Workflow:
1. Collect product/pricing evidence.
2. Collect customer sentiment evidence.
3. Analyze the relevant market category.
4. Synthesize the evidence into a concise executive report.
5. Clearly distinguish observed data, inference, and recommendations.
""".strip()

    async def run_analysis(
        self,
        product_name: str,
        competitors: Optional[List[str]] = None,
        market_segment: Optional[str] = None,
    ) -> AgentResponse:
        competitors_str = ", ".join(competitors or []) or "None"
        segment_str = market_segment or "General"
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"Analyze product: {product_name}\n"
                    f"Competitors: {competitors_str}\n"
                    f"Market segment: {segment_str}"
                ),
            },
        ]

        tools_schema = self.registry.get_all_openai_schemas()
        tool_calls_made = 0
        trace: list[ToolExecution] = []
        final_report = "Analysis could not be completed."

        for _ in range(self.max_iterations):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",
            )
            message = response.choices[0].message
            messages.append(message)

            if not message.tool_calls:
                final_report = message.content or "Analysis completed without a report."
                break

            for tool_call in message.tool_calls:
                tool_calls_made += 1
                name = tool_call.function.name
                started = time.perf_counter()
                error: Optional[str] = None

                try:
                    tool = self.registry.get_tool(name)
                    if not tool:
                        raise ValueError(f"Unknown tool: {name}")

                    raw_args = json.loads(tool_call.function.arguments or "{}")
                    validated_args = tool.args_schema.model_validate(raw_args)
                    result = await tool.run(**validated_args.model_dump())
                except (json.JSONDecodeError, ValueError, TypeError) as exc:
                    error = str(exc)
                    result = {"error": error}
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    result = {"error": error}

                duration_ms = (time.perf_counter() - started) * 1000
                trace.append(
                    ToolExecution(
                        tool_name=name,
                        status="failed" if error else "success",
                        duration_ms=round(duration_ms, 2),
                        error=error,
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result, default=str),
                    }
                )
        else:
            final_report = (
                "Analysis stopped after reaching the maximum agent iterations. "
                "Use the execution trace to inspect incomplete tool execution."
            )

        return AgentResponse(
            report=final_report,
            tool_calls_made=tool_calls_made,
            execution_trace=trace,
        )
