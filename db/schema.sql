
-- PostgreSQL schema for ROS2-MQTT Robot Gateway

CREATE TABLE IF NOT EXISTS command_logs (
    id BIGSERIAL PRIMARY KEY,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    command_id TEXT,
    linear_x DOUBLE PRECISION,
    angular_z DOUBLE PRECISION,
    status TEXT NOT NULL CHECK (
        status IN ('ACCEPTED', 'REJECTED', 'DUPLICATE')
    ),
    reason TEXT
);
