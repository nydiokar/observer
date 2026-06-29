from pathlib import Path


SCHEMA_PATH = Path("src/db/migrations/001_initial_schema.sql")


def test_non_vintage_observation_uniqueness_preserves_retrieval_day():
    schema = SCHEMA_PATH.read_text()

    assert "retrieved_on      DATE NOT NULL" in schema
    assert "series_id, observation_date, source_name, retrieved_on" in schema
    assert "WHERE vintage_date IS NULL" in schema


def test_derived_metrics_support_basket_scope():
    schema = SCHEMA_PATH.read_text()

    assert "basket_name        TEXT REFERENCES baskets(name)" in schema
    assert "uq_derived_metric_scope" in schema
    assert "COALESCE(instrument_id, -1)" in schema
    assert "COALESCE(series_id, '')" in schema
    assert "COALESCE(basket_name, '')" in schema
