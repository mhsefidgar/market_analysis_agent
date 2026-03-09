import pytest
from agent.orchestrator import MarketAnalysisOrchestrator
from agent.tools import get_default_registry

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    registry = get_default_registry()
    orchestrator = MarketAnalysisOrchestrator(registry=registry)
    assert "gpt" in orchestrator.model or orchestrator.model is not None
    assert len(orchestrator.registry.tools) == 4
