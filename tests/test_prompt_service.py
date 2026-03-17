from app.services.prompt_service import PromptService


def test_prompt_service_builds_analysis_prompt() -> None:
    service = PromptService()
    prompt = service.build_analysis_prompt("sales_diagnostics", "revenue_delta_pct=-12.4")
    assert "매출 변화 원인" in prompt
    assert "revenue_delta_pct=-12.4" in prompt


def test_prompt_service_renders_strategy_lead_text() -> None:
    service = PromptService()
    summary = service.render_strategy_summary(
        "menu_pricing",
        context="menu_id=M001",
        lead="가격 인상 테스트가 적합합니다.",
    )
    assert summary == "가격 인상 테스트가 적합합니다."
