from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SeriesRegistry(Base):
    __tablename__ = "series_registry"

    series_id: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    engine: Mapped[str] = mapped_column(Text, nullable=False)
    data_class: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_series_code: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    access_type: Mapped[str] = mapped_column(Text, nullable=False)
    license_class: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False)
    is_direct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    calculation_notes: Mapped[str | None] = mapped_column(Text)
    fallback_source: Mapped[str | None] = mapped_column(Text)
    refresh_policy: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_type: Mapped[str] = mapped_column(Text, nullable=False)
    engine: Mapped[str] = mapped_column(Text, nullable=False)
    basket_name: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Basket(Base):
    __tablename__ = "baskets"

    name: Mapped[str] = mapped_column(Text, primary_key=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    engine: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    members: Mapped[list["BasketMember"]] = relationship(
        back_populates="basket",
        cascade="all, delete-orphan",
    )


class BasketMember(Base):
    __tablename__ = "basket_members"

    basket_name: Mapped[str] = mapped_column(
        Text,
        ForeignKey("baskets.name"),
        primary_key=True,
    )
    ticker: Mapped[str] = mapped_column(
        Text,
        ForeignKey("instruments.ticker"),
        primary_key=True,
    )
    basket: Mapped[Basket] = relationship(back_populates="members")


class RawPayload(Base):
    __tablename__ = "raw_payloads"

    raw_payload_id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_name: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_url_hash: Mapped[str | None] = mapped_column(Text)
    request_params_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response_format: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="success")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SeriesObservation(Base):
    __tablename__ = "series_observations"
    __table_args__ = (
        Index(
            "uq_obs_vintage",
            "series_id",
            "observation_date",
            "vintage_date",
            "source_name",
            unique=True,
            postgresql_where=text("vintage_date IS NOT NULL"),
        ),
        Index(
            "uq_obs_novintage",
            "series_id",
            "observation_date",
            "source_name",
            "retrieved_on",
            unique=True,
            postgresql_where=text("vintage_date IS NULL"),
        ),
        Index("idx_obs_latest", "series_id", text("observation_date DESC"), text("retrieved_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    series_id: Mapped[str] = mapped_column(Text, ForeignKey("series_registry.series_id"), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_series_code: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column(Date)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vintage_date: Mapped[date | None] = mapped_column(Date)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_on: Mapped[date] = mapped_column(Date, nullable=False)
    revision_no: Mapped[int | None] = mapped_column(Integer)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, default="ok")
    raw_payload_id: Mapped[str | None] = mapped_column(Text, ForeignKey("raw_payloads.raw_payload_id"))


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = (UniqueConstraint("instrument_id", "date", "source_name"),)

    id: Mapped[int] = mapped_column(BigInteger)
    instrument_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("instruments.instrument_id"),
        primary_key=True,
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    source_name: Mapped[str] = mapped_column(Text, primary_key=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, default="ok")


class FinancialFact(Base):
    __tablename__ = "financial_facts"
    __table_args__ = (UniqueConstraint("ticker", "period_end", "fact_name", "source_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    cik: Mapped[str | None] = mapped_column(Text)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(Text, nullable=False)
    fact_name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    filing_accession: Mapped[str | None] = mapped_column(Text)
    form_type: Mapped[str | None] = mapped_column(Text)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, default="ok")


class DerivedMetric(Base):
    __tablename__ = "derived_metrics"
    __table_args__ = (
        CheckConstraint(
            "instrument_id IS NOT NULL OR series_id IS NOT NULL OR basket_name IS NOT NULL",
            name="ck_derived_metric_has_scope",
        ),
        Index(
            "uq_derived_metric_scope",
            "metric_id",
            text("COALESCE(instrument_id, -1)"),
            text("COALESCE(series_id, '')"),
            text("COALESCE(basket_name, '')"),
            "date",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    metric_id: Mapped[str] = mapped_column(Text, nullable=False)
    instrument_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("instruments.instrument_id"))
    series_id: Mapped[str | None] = mapped_column(Text, ForeignKey("series_registry.series_id"))
    basket_name: Mapped[str | None] = mapped_column(Text, ForeignKey("baskets.name"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    calculation_version: Mapped[str] = mapped_column(Text, nullable=False)
    input_refs_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, default="ok")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class EarningsEvent(Base):
    __tablename__ = "earnings_events"
    __table_args__ = (UniqueConstraint("ticker", "fiscal_period", "source_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(Text, nullable=False)
    earnings_date: Mapped[date] = mapped_column(Date, nullable=False)
    reported_eps: Mapped[float | None] = mapped_column(Float)
    estimated_eps: Mapped[float | None] = mapped_column(Float)
    eps_surprise: Mapped[float | None] = mapped_column(Float)
    eps_surprise_pct: Mapped[float | None] = mapped_column(Float)
    reported_revenue: Mapped[float | None] = mapped_column(Float)
    estimated_revenue: Mapped[float | None] = mapped_column(Float)
    revenue_surprise: Mapped[float | None] = mapped_column(Float)
    revenue_surprise_pct: Mapped[float | None] = mapped_column(Float)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality_flag: Mapped[str] = mapped_column(Text, nullable=False, default="ok")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    run_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_added: Mapped[int | None] = mapped_column(Integer, default=0)
    records_updated: Mapped[int | None] = mapped_column(Integer, default=0)
    errors: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
