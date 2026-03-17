from app.data.pipelines import normalize_dataset, profile_dataset


def test_normalize_sales_dataset_casts_numeric_fields() -> None:
    rows = normalize_dataset("sales", "app/mock_data/sales_daily.csv")
    assert len(rows) >= 1
    assert isinstance(rows[0]["revenue"], float)
    assert rows[0]["store_id"] == "S001"


def test_profile_review_dataset_returns_counts() -> None:
    profile = profile_dataset("review", "app/mock_data/reviews.csv")
    assert profile["dataset_type"] == "review"
    assert profile["row_count"] >= 1
    assert "rating" in profile["numeric_profiles"]
