from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sales_diagnostics_returns_evidence_and_version() -> None:
    response = client.post(
        "/api/v1/analysis/sales-diagnostics",
        json={
            "store_id": "S001",
            "data_window": {"start": "2026-03-01", "end": "2026-03-14"},
            "record_count": 120,
            "source_name": "sales.csv",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
            "revenue_delta_pct": -12.4,
            "customer_delta_pct": -9.1,
            "avg_ticket_delta_pct": -2.6,
            "channel_delta_pct": -4.0,
            "weather_impact_pct": -3.4,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_type"] == "sales_diagnostics"
    assert len(body["evidence"]) == 3
    assert body["version"]["agent"] == "analysis"


def test_store_intelligence_combines_sales_churn_and_staffing() -> None:
    response = client.post(
        "/api/v1/analysis/store-intelligence",
        json={
            "store_id": "S001",
            "roi_rate": 42.1,
            "avg_order_value": 128000,
            "recent_visit_count": 481,
            "sales_input": {
                "store_id": "S001",
                "data_window": {"start": "2026-03-01", "end": "2026-03-14"},
                "record_count": 120,
                "source_name": "sales.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00",
                "revenue_delta_pct": -12.4,
                "customer_delta_pct": -9.1,
                "avg_ticket_delta_pct": -2.6,
                "channel_delta_pct": -4.0,
                "weather_impact_pct": -3.4,
            },
            "churn_input": {
                "store_id": "S001",
                "data_window": {"start": "2026-03-01", "end": "2026-03-14"},
                "record_count": 120,
                "source_name": "customers.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00",
                "at_risk_customers": 33,
                "delayed_visit_days": 21,
                "avg_visit_cycle_days": 12,
                "coupon_redemption_rate": 0.18,
            },
            "staffing_inputs": [
                {
                    "store_id": "S001",
                    "date": "2026-03-01",
                    "hour": 12,
                    "sales": 320000,
                    "staff_actual": 3,
                    "staff_recommended": 5,
                    "source_name": "staffing_hourly.csv",
                    "uploaded_at": "2026-03-15T09:00:00+09:00",
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["store_id"] == "S001"
    assert body["sales"]["analysis_type"] == "sales_diagnostics"
    assert body["churn"]["analysis_type"] == "churn_insight"
    assert len(body["staffing"]) == 1
    assert len(body["priority_actions"]) >= 3


def test_retention_strategy_builds_actions() -> None:
    response = client.post(
        "/api/v1/strategy/retention-offer",
        json={
            "store_id": "S001",
            "segment_name": "이탈우려군",
            "customer_count": 48,
            "avg_margin_per_customer": 18000,
            "churn_risk_level": "high",
            "coupon_budget": 120000,
            "source_name": "rfm.csv",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_type"] == "retention_offer"
    assert body["actions"][0]["priority"] == "P0"


def test_menu_pricing_strategy_uses_menu_baseline() -> None:
    response = client.post(
        "/api/v1/strategy/menu-pricing",
        json={
            "store_id": "S001",
            "menu_id": "M001",
            "price": 9900,
            "cost": 7000,
            "quantity": 450,
            "margin_rate": 0.29,
            "category": "main",
            "source_name": "menu_metrics.csv",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_type"] == "menu_pricing"
    assert body["action"] == "price_up_test"
    assert body["recommended_price_min"] > 9900


def test_target_validation_excludes_invalid_customers() -> None:
    response = client.post(
        "/api/v1/campaigns/validate-targets",
        json={
            "campaign_id": "CMP-1",
            "targets": [
                {"customer_id": "C1", "consent": True, "cooldown_days": 10, "duplicate": False},
                {"customer_id": "C2", "consent": False, "cooldown_days": 10, "duplicate": False},
                {"customer_id": "C3", "consent": True, "cooldown_days": 3, "duplicate": False},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid_count"] == 1
    assert body["excluded_count"] == 2


def test_notice_ocr_extracts_checklist() -> None:
    response = client.post(
        "/api/v1/notices/ocr",
        data={
            "raw_text": "3월 20일까지 POS 배너 반영 필수\n포인트 적립 룰 적용",
            "source_name": "notice.txt",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ocr_confidence"] >= 0.9
    assert len(body["required_actions"]) >= 1


def test_workflow_returns_pending_approval_for_retention_recovery() -> None:
    response = client.post(
        "/api/v1/workflows/run",
        json={
            "store_id": "S001",
            "scenario": "retention_recovery",
            "dry_run": True,
            "churn_input": {
                "store_id": "S001",
                "data_window": {"start": "2026-03-01", "end": "2026-03-14"},
                "record_count": 120,
                "source_name": "customers.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00",
                "at_risk_customers": 33,
                "delayed_visit_days": 21,
                "avg_visit_cycle_days": 12,
                "coupon_redemption_rate": 0.18,
            },
            "retention_input": {
                "store_id": "S001",
                "segment_name": "이탈우려군",
                "customer_count": 33,
                "avg_margin_per_customer": 20000,
                "churn_risk_level": "high",
                "coupon_budget": 99000,
                "source_name": "rfm.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_approval"


def test_operations_tuning_workflow_runs_strategy_and_operations() -> None:
    response = client.post(
        "/api/v1/workflows/run",
        json={
            "store_id": "S001",
            "scenario": "operations_tuning",
            "dry_run": True,
            "menu_input": {
                "store_id": "S001",
                "menu_id": "M001",
                "price": 9900,
                "cost": 7000,
                "quantity": 450,
                "margin_rate": 0.29,
                "category": "main",
                "source_name": "menu_metrics.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00"
            },
            "staffing_input": {
                "store_id": "S001",
                "date": "2026-03-01",
                "hour": 12,
                "sales": 320000,
                "staff_actual": 3,
                "staff_recommended": 5,
                "source_name": "staffing_hourly.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00"
            },
            "inventory_input": {
                "store_id": "S001",
                "month": "2026-02",
                "item_id": "I002",
                "system_qty": 90,
                "actual_qty": 80,
                "loss_rate": 0.111,
                "source_name": "inventory_monthly.csv",
                "uploaded_at": "2026-03-15T09:00:00+09:00"
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert "menu_strategy" in body["outputs"]
    assert "staffing" in body["outputs"]
    assert "inventory" in body["outputs"]


def test_staffing_endpoint_uses_baseline_gap_logic() -> None:
    response = client.post(
        "/api/v1/operations/staffing",
        json={
            "store_id": "S001",
            "date": "2026-03-01",
            "hour": 12,
            "sales": 320000,
            "staff_actual": 3,
            "staff_recommended": 5,
            "source_name": "staffing_hourly.csv",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "understaffed"
    assert body["gap"] == 2


def test_inventory_endpoint_returns_reorder_qty() -> None:
    response = client.post(
        "/api/v1/operations/inventory",
        json={
            "store_id": "S001",
            "month": "2026-02",
            "item_id": "I002",
            "system_qty": 90,
            "actual_qty": 80,
            "loss_rate": 0.111,
            "source_name": "inventory_monthly.csv",
            "uploaded_at": "2026-03-15T09:00:00+09:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "high"
    assert body["reorder_qty"] >= 10
