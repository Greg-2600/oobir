CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS price_history (
    ticker TEXT NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    dividends DOUBLE PRECISION,
    stock_splits DOUBLE PRECISION,
    PRIMARY KEY (ticker, date)
);

SELECT create_hypertable('price_history', 'date', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_price_history_ticker_date
    ON price_history (ticker, date DESC);
