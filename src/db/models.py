from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DataClass(str, Enum):
    official_actual = "official_actual"
    vendor_actual = "vendor_actual"
    vendor_estimate = "vendor_estimate"
    derived = "derived"
    manual = "manual"


class Priority(str, Enum):
    core = "core"
    useful = "useful"
    optional = "optional"
    defer = "defer"


class QualityFlag(str, Enum):
    ok = "ok"
    stale = "stale"
    missing = "missing"
    partial = "partial"
    revised = "revised"
    estimated = "estimated"
    vendor_limited = "vendor_limited"
    manual = "manual"
    source_failed = "source_failed"
    parse_failed = "parse_failed"
    mapping_uncertain = "mapping_uncertain"
    license_restricted = "license_restricted"
    missing_inputs = "missing_inputs"
    stale_inputs = "stale_inputs"


class SeriesEntry(BaseModel):
    model_config = {"extra": "ignore"}

    series_id: str
    display_name: str
    engine: str
    data_class: DataClass
    source_name: str
    source_series_code: Optional[str] = None
    frequency: str
    unit: str
    access_type: str
    license_class: str
    priority: Priority
    is_direct: bool = True
    calculation_notes: Optional[str] = None
    fallback_source: Optional[str] = None
    refresh_policy: str
    notes: Optional[str] = None
    enabled: bool = True


class InstrumentEntry(BaseModel):
    ticker: str
    name: str
    instrument_type: str
    engine: str
    basket_name: Optional[str] = None
    enabled: bool = True


class BasketEntry(BaseModel):
    name: str
    display_name: str
    engine: str
    description: Optional[str] = None
    members: list[str]
    enabled: bool = True


class SourceEntry(BaseModel):
    model_config = {"extra": "ignore"}

    name: str
    display_name: str
    tier: int
    access_type: str
    license_class: str
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    rate_limit: Optional[int] = None
    rate_limit_window_seconds: Optional[int] = None
    enabled: bool = True
