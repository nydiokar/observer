from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


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


class Engine(str, Enum):
    macro_fed = "macro_fed"
    inflation = "inflation"
    labor = "labor"
    activity = "activity"
    liquidity_fear = "liquidity_fear"
    credit_rates = "credit_rates"
    commodities = "commodities"
    valuation = "valuation"
    earnings = "earnings"
    ai_semiconductor = "ai_semiconductor"
    balance_sheet = "balance_sheet"
    data_quality = "data_quality"


class Frequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"
    irregular = "irregular"


class AccessType(str, Enum):
    free_official = "free_official"
    free_vendor = "free_vendor"
    freemium = "freemium"
    paid = "paid"
    manual = "manual"
    vendor_restricted = "vendor_restricted"


class LicenseClass(str, Enum):
    public = "public"
    internal_only = "internal_only"
    display_restricted = "display_restricted"
    unknown = "unknown"


class RefreshPolicy(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    release_calendar = "release_calendar"
    manual = "manual"


class InstrumentType(str, Enum):
    equity = "equity"
    ETF = "ETF"
    index = "index"
    basket = "basket"


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
    model_config = ConfigDict(extra="forbid")

    series_id: str
    display_name: str
    engine: Engine
    data_class: DataClass
    source_name: str
    source_series_code: Optional[str] = None
    frequency: Frequency
    unit: str
    access_type: AccessType
    license_class: LicenseClass
    priority: Priority
    is_direct: bool = True
    calculation_notes: Optional[str] = None
    fallback_source: Optional[str] = None
    refresh_policy: RefreshPolicy
    notes: Optional[str] = None
    enabled: bool = True


class InstrumentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    name: str
    instrument_type: InstrumentType
    engine: Engine
    basket_name: Optional[str] = None
    enabled: bool = True


class BasketEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str
    engine: Engine
    description: Optional[str] = None
    members: list[str]
    enabled: bool = True


class SourceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str
    tier: int
    access_type: AccessType
    license_class: LicenseClass
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    rate_limit: Optional[int] = None
    rate_limit_window_seconds: Optional[int] = None
    retry_policy: Optional[dict[str, Any]] = None
    headers: Optional[dict[str, str]] = None
    enabled: bool = True
