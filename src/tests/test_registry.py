from src.db.config import load_baskets, load_instruments, load_series_registry, load_sources
from src.db.models import DataClass


def test_series_ids_unique():
    series = load_series_registry()
    ids = [s.series_id for s in series]
    assert len(ids) == len(set(ids)), f"Duplicate series_ids found"


def test_enabled_series_have_source():
    series = load_series_registry()
    for s in series:
        if s.enabled:
            assert s.source_name, f"Series {s.series_id} is enabled but has no source_name"


def test_enabled_series_have_refresh_policy():
    series = load_series_registry()
    for s in series:
        if s.enabled:
            assert s.refresh_policy, f"Series {s.series_id} is enabled but has no refresh_policy"


def test_derived_series_have_calculation_notes():
    series = load_series_registry()
    for s in series:
        if s.data_class == DataClass.derived:
            assert s.calculation_notes, f"Derived series {s.series_id} missing calculation_notes"


def test_vendor_series_have_license_class():
    series = load_series_registry()
    vendor_access = {"freemium", "paid", "vendor_restricted"}
    for s in series:
        if s.access_type in vendor_access:
            assert s.license_class, f"Vendor series {s.series_id} has no license_class"


def test_required_series_fields_present():
    series = load_series_registry()
    for s in series:
        assert s.series_id, "Series missing series_id"
        assert s.display_name, f"Series {s.series_id} missing display_name"
        assert s.engine, f"Series {s.series_id} missing engine"
        assert s.frequency, f"Series {s.series_id} missing frequency"
        assert s.unit, f"Series {s.series_id} missing unit"
        assert s.priority, f"Series {s.series_id} missing priority"


def test_instrument_tickers_unique():
    instruments = load_instruments()
    tickers = [i.ticker for i in instruments]
    assert len(tickers) == len(set(tickers)), "Duplicate instrument tickers"


def test_basket_members_exist():
    instruments = load_instruments()
    ticker_set = {i.ticker for i in instruments}
    baskets = load_baskets()
    for b in baskets:
        for member in b.members:
            assert member in ticker_set, f"Basket {b.name} member {member} not in instruments"


def test_sources_not_empty():
    sources = load_sources()
    assert len(sources) > 0, "No sources loaded"
