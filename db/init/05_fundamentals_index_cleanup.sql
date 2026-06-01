-- Remove redundant fundamentals indexes that are not used by current query plans.
-- Safe to run multiple times.

DROP INDEX IF EXISTS idx_fundamentals_sector_ticker_fetched;
DROP INDEX IF EXISTS idx_fundamentals_market_cap;
DROP INDEX IF EXISTS idx_fundamentals_trailing_pe_pos;
DROP INDEX IF EXISTS idx_fundamentals_dividend_yield;
DROP INDEX IF EXISTS idx_fundamentals_return_on_equity;
DROP INDEX IF EXISTS idx_fundamentals_debt_to_equity;
DROP INDEX IF EXISTS idx_fundamentals_market_cap_ticker_fetched;
DROP INDEX IF EXISTS idx_fundamentals_trailing_pe_ticker_fetched;
DROP INDEX IF EXISTS idx_fundamentals_dividend_ticker_fetched;
DROP INDEX IF EXISTS idx_fundamentals_roe_ticker_fetched;
DROP INDEX IF EXISTS idx_fundamentals_dte_ticker_fetched;
