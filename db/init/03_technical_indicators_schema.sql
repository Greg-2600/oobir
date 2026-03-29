CREATE TABLE IF NOT EXISTS technical_indicators (
    ticker          TEXT             NOT NULL,
    date            TIMESTAMPTZ      NOT NULL,
    -- Moving averages
    sma_20          DOUBLE PRECISION,
    sma_50          DOUBLE PRECISION,
    -- RSI
    rsi_14          DOUBLE PRECISION,
    -- MACD
    macd            DOUBLE PRECISION,
    macd_signal     DOUBLE PRECISION,
    macd_histogram  DOUBLE PRECISION,
    -- Bollinger Bands
    bb_upper        DOUBLE PRECISION,
    bb_middle       DOUBLE PRECISION,
    bb_lower        DOUBLE PRECISION,
    -- Volume
    volume_avg_20   DOUBLE PRECISION,
    volume_ratio    DOUBLE PRECISION,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_technical_indicators_ticker_date
    ON technical_indicators (ticker, date DESC);
