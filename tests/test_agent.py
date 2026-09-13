import os

import pytest

from agent.orchestrator import MarketAnalysisOrchestrator
from agent.tools import get_default_registry


def test_orchestrator_initialization(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    registry = get_default_registry()
    orchestrator = MarketAnalysisOrchestrator(registry=registry)

    assert orchestrator.model
    assert orchestrator.max_iterations == 8
    assert len(orchestrator.registry.tools) == 4
    assert {"web_scraper", "sentiment_analyzer", "market_trend_analyzer", "report_generator"} == set(
        orchestrator.registry.tools
    )


def test_missing_api_key_fails_fast(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        MarketAnalysisOrchestrator()
