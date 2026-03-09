import pytest
from agent.tools import WebScraperTool, SentimentAnalyzerTool, MarketTrendAnalyzerTool, ReportGeneratorTool

@pytest.mark.asyncio
async def test_web_scraper_tool():
    tool = WebScraperTool()
    result = await tool.run(product_name="Test Product")
    assert result["product"] == "Test Product"
    assert "pricing_data" in result
    assert "Amazon" in result["pricing_data"]

@pytest.mark.asyncio
async def test_sentiment_tool():
    tool = SentimentAnalyzerTool()
    result = await tool.run(product_name="Test Product")
    assert result["product"] == "Test Product"
    assert "overall_sentiment" in result

@pytest.mark.asyncio
async def test_market_trend_tool():
    tool = MarketTrendAnalyzerTool()
    result = await tool.run(category="Electronics")
    assert result["category"] == "Electronics"
    assert "trend" in result

@pytest.mark.asyncio
async def test_report_generator_tool():
    tool = ReportGeneratorTool()
    result = await tool.run(insights="Great product overall.")
    assert "status" in result
    assert "report_preview" in result
