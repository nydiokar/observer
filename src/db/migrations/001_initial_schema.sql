CREATE TABLE IF NOT EXISTS series_registry (
    series_id          TEXT PRIMARY KEY,
    display_name       TEXT NOT NULL,
    engine             TEXT NOT NULL,
    data_class         TEXT NOT NULL,
    source_name        TEXT NOT NULL,
    source_series_code TEXT,
    frequency          TEXT NOT NULL,
    unit               TEXT NOT NULL,
    access_type        TEXT NOT NULL,
    license_class      TEXT NOT NULL,
    priority           TEXT NOT NULL,
    is_direct          BOOLEAN NOT NULL DEFAULT TRUE,
    calculation_notes  TEXT,
    fallback_source    TEXT,
    refresh_policy     TEXT NOT NULL,
    notes              TEXT,
    enabled            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS instruments (
    instrument_id    SERIAL PRIMARY KEY,
    ticker           TEXT NOT NULL UNIQUE,
    name             TEXT NOT NULL,
    instrument_type  TEXT NOT NULL,
    engine           TEXT NOT NULL,
    basket_name      TEXT,
    enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS baskets (
    name         TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    engine       TEXT NOT NULL,
    description  TEXT,
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS basket_members (
    basket_name TEXT NOT NULL REFERENCES baskets(name),
    ticker      TEXT NOT NULL REFERENCES instruments(ticker),
    PRIMARY KEY (basket_name, ticker)
);

CREATE TABLE IF NOT EXISTS raw_payloads (
    raw_payload_id    TEXT PRIMARY KEY,
    source_name       TEXT NOT NULL,
    dataset_name      TEXT NOT NULL,
    retrieved_at      TIMESTAMPTZ NOT NULL,
    request_url_hash  TEXT,
    request_params_json JSONB,
    response_format   TEXT NOT NULL,
    storage_path      TEXT NOT NULL,
    checksum          TEXT,
    status            TEXT NOT NULL DEFAULT 'success',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS series_observations DROP CONSTRAINT IF EXISTS series_observations_raw_payload_id_fkey;
ALTER TABLE raw_payloads ALTER COLUMN raw_payload_id DROP DEFAULT;
ALTER TABLE raw_payloads ALTER COLUMN raw_payload_id TYPE TEXT USING raw_payload_id::TEXT;

CREATE TABLE IF NOT EXISTS series_observations (
    id                BIGSERIAL PRIMARY KEY,
    series_id         TEXT NOT NULL REFERENCES series_registry(series_id),
    observation_date  DATE NOT NULL,
    value             DOUBLE PRECISION NOT NULL,
    unit              TEXT NOT NULL,
    source_name       TEXT NOT NULL,
    source_series_code TEXT,
    release_date      DATE,
    available_at      TIMESTAMPTZ,
    vintage_date      DATE,
    retrieved_at      TIMESTAMPTZ NOT NULL,
    retrieved_on      DATE NOT NULL,
    revision_no       INTEGER,
    quality_flag      TEXT NOT NULL DEFAULT 'ok',
    raw_payload_id    TEXT REFERENCES raw_payloads(raw_payload_id)
);

ALTER TABLE series_observations DROP CONSTRAINT IF EXISTS series_observations_raw_payload_id_fkey;
ALTER TABLE series_observations ADD COLUMN IF NOT EXISTS retrieved_on DATE;
UPDATE series_observations
SET retrieved_on = COALESCE(retrieved_on, retrieved_at::DATE)
WHERE retrieved_on IS NULL;
ALTER TABLE series_observations ALTER COLUMN retrieved_on SET DEFAULT CURRENT_DATE;
ALTER TABLE series_observations ALTER COLUMN retrieved_on SET NOT NULL;
ALTER TABLE series_observations ALTER COLUMN raw_payload_id TYPE TEXT USING raw_payload_id::TEXT;
ALTER TABLE series_observations
    ADD CONSTRAINT series_observations_raw_payload_id_fkey
    FOREIGN KEY (raw_payload_id) REFERENCES raw_payloads(raw_payload_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_obs_vintage
    ON series_observations (series_id, observation_date, vintage_date, source_name)
    WHERE vintage_date IS NOT NULL;

DROP INDEX IF EXISTS uq_obs_novintage;
CREATE UNIQUE INDEX IF NOT EXISTS uq_obs_novintage
    ON series_observations (series_id, observation_date, source_name, retrieved_on)
    WHERE vintage_date IS NULL;

CREATE INDEX IF NOT EXISTS idx_obs_latest
    ON series_observations (series_id, observation_date DESC, retrieved_at DESC);

CREATE TABLE IF NOT EXISTS market_prices (
    id                BIGSERIAL,
    instrument_id     INTEGER NOT NULL REFERENCES instruments(instrument_id),
    date              DATE NOT NULL,
    open              DOUBLE PRECISION,
    high              DOUBLE PRECISION,
    low               DOUBLE PRECISION,
    close             DOUBLE PRECISION NOT NULL,
    adjusted_close    DOUBLE PRECISION,
    volume            BIGINT,
    source_name       TEXT NOT NULL,
    retrieved_at      TIMESTAMPTZ NOT NULL,
    quality_flag      TEXT NOT NULL DEFAULT 'ok',
    PRIMARY KEY (instrument_id, date, source_name)
);

CREATE TABLE IF NOT EXISTS financial_facts (
    id               BIGSERIAL PRIMARY KEY,
    ticker           TEXT NOT NULL,
    cik              TEXT,
    period_end       DATE NOT NULL,
    fiscal_year      INTEGER NOT NULL,
    fiscal_period    TEXT NOT NULL,
    fact_name        TEXT NOT NULL,
    value            DOUBLE PRECISION NOT NULL,
    unit             TEXT NOT NULL,
    source_name      TEXT NOT NULL,
    filing_accession TEXT,
    form_type        TEXT,
    filed_at         TIMESTAMPTZ,
    accepted_at      TIMESTAMPTZ,
    retrieved_at     TIMESTAMPTZ NOT NULL,
    quality_flag     TEXT NOT NULL DEFAULT 'ok',
    UNIQUE (ticker, period_end, fact_name, source_name)
);

CREATE TABLE IF NOT EXISTS derived_metrics (
    id                 BIGSERIAL PRIMARY KEY,
    metric_id          TEXT NOT NULL,
    instrument_id      INTEGER REFERENCES instruments(instrument_id),
    series_id          TEXT REFERENCES series_registry(series_id),
    basket_name        TEXT REFERENCES baskets(name),
    date               DATE NOT NULL,
    value              DOUBLE PRECISION,
    calculation_version TEXT NOT NULL,
    input_refs_json    JSONB,
    quality_flag       TEXT NOT NULL DEFAULT 'ok',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        instrument_id IS NOT NULL
        OR series_id IS NOT NULL
        OR basket_name IS NOT NULL
    )
);

ALTER TABLE derived_metrics ADD COLUMN IF NOT EXISTS basket_name TEXT REFERENCES baskets(name);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_derived_metric_has_scope'
    ) THEN
        ALTER TABLE derived_metrics
            ADD CONSTRAINT ck_derived_metric_has_scope
            CHECK (
                instrument_id IS NOT NULL
                OR series_id IS NOT NULL
                OR basket_name IS NOT NULL
            );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_derived_metric_scope
    ON derived_metrics (
        metric_id,
        COALESCE(instrument_id, -1),
        COALESCE(series_id, ''),
        COALESCE(basket_name, ''),
        date
    );

CREATE TABLE IF NOT EXISTS earnings_events (
    id                 BIGSERIAL PRIMARY KEY,
    ticker             TEXT NOT NULL,
    fiscal_period      TEXT NOT NULL,
    earnings_date      DATE NOT NULL,
    reported_eps       DOUBLE PRECISION,
    estimated_eps      DOUBLE PRECISION,
    eps_surprise       DOUBLE PRECISION,
    eps_surprise_pct   DOUBLE PRECISION,
    reported_revenue   DOUBLE PRECISION,
    estimated_revenue  DOUBLE PRECISION,
    revenue_surprise   DOUBLE PRECISION,
    revenue_surprise_pct DOUBLE PRECISION,
    source_name        TEXT NOT NULL,
    retrieved_at       TIMESTAMPTZ NOT NULL,
    quality_flag       TEXT NOT NULL DEFAULT 'ok',
    UNIQUE (ticker, fiscal_period, source_name)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id         SERIAL PRIMARY KEY,
    source_name    TEXT NOT NULL,
    run_type       TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'running',
    started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at    TIMESTAMPTZ,
    records_added  INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    errors         JSONB,
    notes          TEXT
);
