from app.ml.features.inventory import InventoryFeatures, inventory_risk_level, reorder_quantity
from app.ml.features.menu import MenuFeatures, classify_menu_action, pricing_signal
from app.ml.features.sales import SalesRecord, sales_factor_breakdown
from app.ml.features.staffing import StaffingFeatures, opportunity_cost, staffing_status
from app.ml.features.churn import ChurnFeatures, build_churn_score, classify_churn_risk
from app.ml.features.review import score_review_sentiment
from app.ml.inference.baseline_models import (
    predict_anomalies,
    predict_churn,
    predict_inventory,
    predict_menu_strategy,
    predict_review_sentiment,
    predict_sales_factors,
    predict_staffing,
)


def test_churn_score_high_risk_customer() -> None:
    score = build_churn_score(
        ChurnFeatures(
            customer_id="C100",
            store_id="S001",
            recency=45,
            frequency=2,
            monetary=20000,
            last_visit_days=47,
            coupon_use_rate=0.0,
        )
    )
    assert score >= 70
    assert classify_churn_risk(score) == "high"


def test_review_sentiment_negative_keyword_match() -> None:
    sentiment, confidence = score_review_sentiment("배달이 늦고 포인트 누락이 있어 아쉬웠어요")
    assert sentiment == "negative"
    assert confidence >= 0.65


def test_mock_predictions_load_successfully() -> None:
    churn_predictions = predict_churn("app/mock_data/customer_rfm.csv")
    review_predictions = predict_review_sentiment("app/mock_data/reviews.csv")
    anomaly_predictions = predict_anomalies("app/mock_data/anomalies.csv")
    sales_predictions = predict_sales_factors("app/mock_data/sales_daily.csv")
    menu_predictions = predict_menu_strategy("app/mock_data/menu_metrics.csv")
    staffing_predictions = predict_staffing("app/mock_data/staffing_hourly.csv")
    inventory_predictions = predict_inventory("app/mock_data/inventory_monthly.csv")

    assert len(churn_predictions) >= 1
    assert len(review_predictions) >= 1
    assert len(anomaly_predictions) >= 1
    assert len(sales_predictions) >= 1
    assert len(menu_predictions) >= 1
    assert len(staffing_predictions) >= 1
    assert len(inventory_predictions) >= 1


def test_sales_factor_breakdown_returns_top_factors() -> None:
    breakdown = sales_factor_breakdown(
        [
            SalesRecord("2026-01-01", "S001", 1500000, 180, 175, 8570, "offline", "sunny", 0),
            SalesRecord("2026-01-02", "S001", 1480000, 178, 172, 8600, "offline", "cloudy", 0),
            SalesRecord("2026-01-03", "S001", 1260000, 160, 145, 8690, "delivery", "rain", 1),
            SalesRecord("2026-01-04", "S001", 1220000, 155, 138, 8840, "delivery", "rain", 1),
        ]
    )
    assert breakdown["dominant_factor"] in breakdown["top_factors"]
    assert len(breakdown["top_factors"]) == 3


def test_menu_strategy_identifies_low_margin_item() -> None:
    features = MenuFeatures(
        menu_id="M100",
        store_id="S001",
        price=9900,
        cost=7000,
        quantity=450,
        margin_rate=0.29,
        category="main",
    )
    signal = pricing_signal(features)
    assert signal == "raise_price"
    assert classify_menu_action(features, signal) == "price_up_test"


def test_staffing_status_and_cost_for_understaffed_slot() -> None:
    features = StaffingFeatures(
        date="2026-03-01",
        store_id="S001",
        hour=12,
        sales=320000,
        staff_actual=3,
        staff_recommended=5,
    )
    assert staffing_status(features) == "understaffed"
    assert opportunity_cost(features) > 0


def test_inventory_risk_and_reorder_for_high_loss_item() -> None:
    features = InventoryFeatures(
        month="2026-02",
        store_id="S001",
        item_id="I002",
        system_qty=90,
        actual_qty=80,
        loss_rate=0.111,
    )
    assert inventory_risk_level(features) == "high"
    assert reorder_quantity(features) >= 10
