CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE TABLE assets (
 id text PRIMARY KEY, name text NOT NULL, production_line text NOT NULL,
 criticality smallint NOT NULL CHECK (criticality BETWEEN 1 AND 5)
);
CREATE TABLE sensors (
 id text PRIMARY KEY, asset_id text NOT NULL REFERENCES assets(id),
 sensor_type text NOT NULL, unit text NOT NULL,
 sample_seconds integer NOT NULL CHECK(sample_seconds > 0),
 enabled boolean NOT NULL DEFAULT true
);
CREATE TABLE telemetry (
 time timestamptz NOT NULL CHECK (isfinite(time)),
 sensor_id text NOT NULL REFERENCES sensors(id),
 value double precision NOT NULL CHECK (value > '-Infinity'::float8 AND value < 'Infinity'::float8),
 quality smallint NOT NULL CHECK (quality BETWEEN 0 AND 100),
 seq bigint NOT NULL CHECK (seq >= 0),
 received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(sensor_id,time)
);
SELECT create_hypertable('telemetry','time',chunk_time_interval => INTERVAL '1 day');
CREATE INDEX telemetry_sensor_time_idx ON telemetry(sensor_id,time DESC);
CREATE TABLE sensor_thresholds (
 sensor_id text PRIMARY KEY REFERENCES sensors(id),
 warn_low double precision, warn_high double precision,
 critical_low double precision, critical_high double precision,
 CHECK(warn_low IS NULL OR (warn_low > '-Infinity'::float8 AND warn_low < 'Infinity'::float8)),
 CHECK(warn_high IS NULL OR (warn_high > '-Infinity'::float8 AND warn_high < 'Infinity'::float8)),
 CHECK(critical_low IS NULL OR (critical_low > '-Infinity'::float8 AND critical_low < 'Infinity'::float8)),
 CHECK(critical_high IS NULL OR (critical_high > '-Infinity'::float8 AND critical_high < 'Infinity'::float8)),
 CHECK(critical_high IS NULL OR warn_high IS NULL OR critical_high > warn_high),
 CHECK(critical_low IS NULL OR warn_low IS NULL OR critical_low < warn_low)
);
CREATE TABLE alarms (
 id bigserial PRIMARY KEY, sensor_id text NOT NULL REFERENCES sensors(id),
 opened_at timestamptz NOT NULL, closed_at timestamptz,
 severity text NOT NULL CHECK(severity IN ('WARN','CRITICAL')),
 state text NOT NULL DEFAULT 'OPEN' CHECK(state IN ('OPEN','ACK','CLOSED')),
 value double precision NOT NULL CHECK(value > '-Infinity'::float8 AND value < 'Infinity'::float8),
 message text NOT NULL,
 CHECK((state = 'CLOSED') = (closed_at IS NOT NULL)),
 CHECK(closed_at IS NULL OR closed_at >= opened_at)
);
CREATE UNIQUE INDEX alarms_one_active ON alarms(sensor_id) WHERE state IN ('OPEN','ACK');
CREATE INDEX alarms_opened_idx ON alarms(opened_at DESC);
