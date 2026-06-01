-- Additional fundamentals indexes for production query patterns.
-- Safe to run multiple times.

-- Latest-row access pattern: fast newest snapshot lookups per ticker.
CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker_fetched_covering
    ON fundamentals (ticker, fetched_at DESC)
    INCLUDE (
        sector,
        market_cap,
        trailing_pe,
        dividend_yield,
        return_on_equity,
        debt_to_equity,
        current_price
    );

-- Sector and distinct-sector queries.
CREATE INDEX IF NOT EXISTS idx_fundamentals_sector_only
    ON fundamentals (sector)
    WHERE sector IS NOT NULL;
