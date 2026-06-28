import sys

from src.db.config import load_baskets, load_instruments, load_series_registry, load_sources
from src.db.models import DataClass


def validate():
    errors = []

    # Validate sources
    try:
        sources = load_sources()
        source_names = {s.name for s in sources}
    except Exception as e:
        errors.append(f"Failed to load sources.yaml: {e}")
        sources = []
        source_names = set()

    # Validate series
    try:
        series = load_series_registry()
    except Exception as e:
        errors.append(f"Failed to load series_registry.yaml: {e}")
        series = []

    ids = [s.series_id for s in series]
    dup_ids = set(i for i in ids if ids.count(i) > 1)
    if dup_ids:
        errors.append(f"Duplicate series_ids: {dup_ids}")

    for s in series:
        if not s.series_id:
            errors.append("Series missing series_id")
        if not s.display_name:
            errors.append(f"{s.series_id}: missing display_name")
        if not s.engine:
            errors.append(f"{s.series_id}: missing engine")
        if not s.source_name:
            errors.append(f"{s.series_id}: missing source_name")
        if s.source_name and s.source_name not in source_names:
            errors.append(f"{s.series_id}: unknown source_name '{s.source_name}'")
        if not s.frequency:
            errors.append(f"{s.series_id}: missing frequency")
        if not s.unit:
            errors.append(f"{s.series_id}: missing unit")
        if not s.refresh_policy:
            errors.append(f"{s.series_id}: missing refresh_policy")
        if s.enabled and not s.source_name:
            errors.append(f"{s.series_id}: enabled but missing source_name")
        if s.enabled and not s.refresh_policy:
            errors.append(f"{s.series_id}: enabled but missing refresh_policy")
        if s.data_class == DataClass.derived and not s.calculation_notes:
            errors.append(f"{s.series_id}: derived metric missing calculation_notes")
        if s.data_class in (DataClass.vendor_actual, DataClass.vendor_estimate) and s.license_class == "public":
            errors.append(f"{s.series_id}: vendor metric should not be public license")
        code_sources = {"FRED", "ALFRED", "BLS", "BEA", "EIA"}
        if s.is_direct and s.source_name in code_sources and not s.source_series_code:
            errors.append(f"{s.series_id}: direct metric from {s.source_name} missing source_series_code")

    # Validate instruments
    try:
        instruments = load_instruments()
        instrument_tickers = {i.ticker for i in instruments}
    except Exception as e:
        errors.append(f"Failed to load instruments.yaml: {e}")
        instruments = []
        instrument_tickers = set()

    ticker_list = [i.ticker for i in instruments]
    dup_tickers = set(t for t in ticker_list if ticker_list.count(t) > 1)
    if dup_tickers:
        errors.append(f"Duplicate tickers: {dup_tickers}")

    for i in instruments:
        if i.instrument_type not in ("equity", "ETF", "index", "basket"):
            errors.append(f"{i.ticker}: invalid instrument_type '{i.instrument_type}'")

    # Validate baskets
    try:
        baskets = load_baskets()
    except Exception as e:
        errors.append(f"Failed to load baskets.yaml: {e}")
        baskets = []

    basket_names = [b.name for b in baskets]
    dup_baskets = set(n for n in basket_names if basket_names.count(n) > 1)
    if dup_baskets:
        errors.append(f"Duplicate basket names: {dup_baskets}")

    for b in baskets:
        for member in b.members:
            if member not in instrument_tickers:
                errors.append(f"Basket '{b.name}' member '{member}' not found in instruments")

    return errors


def main():
    errors = validate()
    if errors:
        print("Registry validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Registry validation PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
