CREATE TABLE IF NOT EXISTS plans (
    plan_hash       TEXT PRIMARY KEY,
    request_json    JSONB NOT NULL,
    response_json   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS plans_created_at_idx ON plans (created_at DESC);
