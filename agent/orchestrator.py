import json
import os
from typing import Dict, Any, List
from openai import AsyncOpenAI
from .tools import get_default_registry, ToolRegistry
from .models import AgentResponse

class MarketAnalysisOrchestrator:
    def __init__(self, model: str = "gpt-4o-mini", registry: ToolRegistry = None):
        # Allow configuring via environment variables for various providers
        api_key = os.getenv("OPENAI_API_KEY", "dummy-key-for-testing")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = os.getenv("MODEL_NAME", model)
        self.registry = registry or get_default_registry()
        self.system_prompt = """
You are an expert E-commerce Market Analysis Agent.
Your goal is to provide comprehensive strategic reports on specific products or markets.
You have access to several specialized tools:
- web_scraper: Collects prices and product information.
- sentiment_analyzer: Analyzes customer reviews.
- market_trend_analyzer: Analyzes price and popularity trends.
- report_generator: Compiles raw data into a structured report.

Follow these steps to complete an analysis request:
1. Use web_scraper to gather base product data.
2. Use sentiment_analyzer to understand customer perception.
3. Use market_trend_analyzer (with the appropriate category) to understand the landscape.
4. Pass all gathered insights to the report_generator tool to create the final synthesized report.
5. Return the generated report to the user summarizing your actions.

Always use the tools to gather data. Do not make up product data.
"""

    async def run_analysis(self, product_name: str, competitors: List[str] = None, market_segment: str = None) -> AgentResponse:
        competitors_str = ", ".join(competitors) if competitors else "None"
        market_segment_str = market_segment if market_segment else "General"
        
        user_msg = f"Please analyze the following product: {product_name}.\nCompetitors: {competitors_str}.\nMarket segment: {market_segment_str}."
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_msg}
        ]
        
        tools_schema = self.registry.get_all_openai_schemas()
        
        tool_calls_made = 0
        final_report = "Analysis failed or incomplete."
        
        # Max iterations to prevent infinite loops
        for _ in range(10):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if not message.tool_calls:
                # Agent has finished and replied with regular text
                final_report = message.content
                break
                
            for tool_call in message.tool_calls:
                tool_calls_made += 1
                function_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                tool = self.registry.get_tool(function_name)
                if not tool:
                    tool_result = {"error": f"Tool {function_name} not found"}
                else:
                    try:
                        validated_args = tool.args_schema(**tool_args)
                        tool_result = await tool.run(**validated_args.model_dump())
                    except Exception as e:
                        tool_result = {"error": str(e)}
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })
                
        return AgentResponse(report=final_report, tool_calls_made=tool_calls_made)
