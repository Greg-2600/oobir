CREATE TABLE IF NOT EXISTS fundamentals (
    ticker      TEXT        NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Identification
    short_name          TEXT,
    long_name           TEXT,
    sector              TEXT,
    industry            TEXT,
    exchange            TEXT,
    currency            TEXT,
    -- Valuation
    market_cap          BIGINT,
    enterprise_value    BIGINT,
    trailing_pe         DOUBLE PRECISION,
    forward_pe          DOUBLE PRECISION,
    peg_ratio           DOUBLE PRECISION,
    price_to_book       DOUBLE PRECISION,
    price_to_sales      DOUBLE PRECISION,
    enterprise_to_ebitda DOUBLE PRECISION,
    -- Earnings & profitability
    trailing_eps        DOUBLE PRECISION,
    forward_eps         DOUBLE PRECISION,
    profit_margins      DOUBLE PRECISION,
    operating_margins   DOUBLE PRECISION,
    gross_margins       DOUBLE PRECISION,
    return_on_equity    DOUBLE PRECISION,
    return_on_assets    DOUBLE PRECISION,
    -- Revenue & income
    total_revenue       BIGINT,
    revenue_per_share   DOUBLE PRECISION,
    revenue_growth      DOUBLE PRECISION,
    earnings_growth     DOUBLE PRECISION,
    ebitda              BIGINT,
    net_income          BIGINT,
    free_cashflow       BIGINT,
    operating_cashflow  BIGINT,
    -- Balance sheet
    total_cash          BIGINT,
    total_debt          BIGINT,
    total_assets        BIGINT,
    book_value          DOUBLE PRECISION,
    current_ratio       DOUBLE PRECISION,
    debt_to_equity      DOUBLE PRECISION,
    -- Dividends
    dividend_yield      DOUBLE PRECISION,
    dividend_rate       DOUBLE PRECISION,
    payout_ratio        DOUBLE PRECISION,
    ex_dividend_date    TIMESTAMPTZ,
    -- Price context at fetch time
    current_price       DOUBLE PRECISION,
    previous_close      DOUBLE PRECISION,
    fifty_two_week_high DOUBLE PRECISION,
    fifty_two_week_low  DOUBLE PRECISION,
    fifty_day_average   DOUBLE PRECISION,
    two_hundred_day_average DOUBLE PRECISION,
    -- Analyst
    target_high_price   DOUBLE PRECISION,
    target_low_price    DOUBLE PRECISION,
    target_mean_price   DOUBLE PRECISION,
    target_median_price DOUBLE PRECISION,
    recommendation_key  TEXT,
    number_of_analyst_opinions INTEGER,
    -- Full raw data for anything not captured above
    raw_info            JSONB,
    PRIMARY KEY (ticker, fetched_at)
);

CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker
    ON fundamentals (ticker, fetched_at DESC);
