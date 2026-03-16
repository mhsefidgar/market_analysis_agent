# ---------------------------------------------------
# ----The current code uses the strategy pattern ----
# ---------------------------------------------------

from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
import random
import asyncio

# ---- Tool Abstract Class --
class Tool(ABC):
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel]

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        pass

    def get_openai_schema(self) -> Dict[str, Any]:
        """Convert the tool's Pydantic schema to OpenAI function calling format."""
        schema = self.args_schema.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": schema.get("type", "object"),
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
            }
        }

# --- Tool Schemas ---
class WebScraperSchema(BaseModel):
    product_name: str = Field(..., description="The name of the product to scrape")
    platforms: list[str] = Field(default=["Amazon", "eBay", "Walmart"], description="Platforms to scrape")

class SentimentSchema(BaseModel):
    product_name: str = Field(..., description="The name of the product to analyze sentiment for")

class MarketTrendSchema(BaseModel):
    category: str = Field(..., description="The product category to analyze trends for")

class ReportGeneratorSchema(BaseModel):
    insights: str = Field(..., description="Compiled insights to format into a report")

# --- Tool Implementations ---
class WebScraperTool(Tool):
    name = "web_scraper"
    description = "Collects prices and basic product info across specified e-commerce platforms."
    args_schema = WebScraperSchema

    async def run(self, product_name: str, platforms: list[str] = None) -> Dict[str, Any]:
        await asyncio.sleep(0.5) # Simulate network call
        if not platforms:
            platforms = ["Amazon", "eBay", "Walmart"]
        
        results = {}
        for platform in platforms:
            results[platform] = {
                "price": round(random.uniform(50.0, 500.0), 2),
                "in_stock": random.choice([True, True, False])
            }
        return {"product": product_name, "pricing_data": results}

class SentimentAnalyzerTool(Tool):
    name = "sentiment_analyzer"
    description = "Analyzes customer reviews and extracts sentiment insights."
    args_schema = SentimentSchema

    async def run(self, product_name: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "product": product_name,
            "overall_sentiment": random.choice(["Positive", "Slightly Positive", "Neutral", "Mixed"]),
            "average_rating": round(random.uniform(3.5, 4.9), 1),
            "key_themes": ["quality", "price-to-value", "shipping speed"]
        }

class MarketTrendAnalyzerTool(Tool):
    name = "market_trend_analyzer"
    description = "Analyzes price and popularity trends over time for a category."
    args_schema = MarketTrendSchema

    async def run(self, category: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "category": category,
            "trend": random.choice(["Upward", "Stable", "Downward"]),
            "momentum_score": random.randint(1, 100),
            "seasonality": "High in Q4"
        }

class ReportGeneratorTool(Tool):
    name = "report_generator"
    description = "Compiles raw data and insights into a structured mock report."
    args_schema = ReportGeneratorSchema

    async def run(self, insights: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "status": "Report generated",
            "report_preview": f"## Executive Summary\n{insights[:100]}...\n\n### Detailed Findings\nData synthesized successfully."
        }

# Tool Registry
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)

    def get_all_openai_schemas(self) -> list[Dict[str, Any]]:
        return [tool.get_openai_schema() for tool in self.tools.values()]
        
# -----------------------------       
# ----- registery pattern -----
# -----------------------------

def get_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(WebScraperTool())
    registry.register(SentimentAnalyzerTool())
    registry.register(MarketTrendAnalyzerTool())
    registry.register(ReportGeneratorTool())
    return registry
