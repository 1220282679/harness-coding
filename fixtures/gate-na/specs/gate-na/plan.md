# gate-na plan

Approach: review the idempotency of migrations/001_init.sql (full IF NOT EXISTS coverage), run the migration against a local psql and verify the \dt output; lint + test gates run as usual, type/format are skipped per the spec's Gate exemptions (chain-wide)
