-- meridian POC schema v1
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health_probe (
  id INT PRIMARY KEY,
  note TEXT NOT NULL
);

INSERT INTO health_probe (id, note)
VALUES (1, 'synthetic')
ON CONFLICT (id) DO NOTHING;
