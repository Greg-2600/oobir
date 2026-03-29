-- Increase lock resources to avoid "out of shared memory" during large queries
ALTER SYSTEM SET max_locks_per_transaction = 512;
