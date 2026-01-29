PRAGMA foreign_keys = ON;
-- Ground stations
CREATE TABLE IF NOT EXISTS ground_stations (
    gs_id INTEGER PRIMARY KEY AUTOINCREMENT,
    gs_code TEXT NOT NULL UNIQUE,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    source TEXT NOT NULL,
    -- (MANUAL, AWS, SATNOGS etc.)
    status TEXT NOT NULL,
    -- (ACTIVE/INACTIVE)
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (lat, lon)
);
-- Satellites
CREATE TABLE IF NOT EXISTS satellites (
    s_id INTEGER PRIMARY KEY AUTOINCREMENT,
    s_name TEXT NOT NULL,
    norad_id INTEGER NOT NULL UNIQUE,
    tle_line1 TEXT,
    tle_line2 TEXT,
    tle_updated_at TIMESTAMP,
    mode TEXT,
    -- (SAFE | NOMINAL | PAYLOAD)
    health_status TEXT,
    -- (OK | DEGRADED | UNKNOWN)
    last_contact_time TIMESTAMP,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Missions
CREATE TABLE IF NOT EXISTS missions (
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_name TEXT NOT NULL,
    owner TEXT,
    priority TEXT,
    -- ("low" | "medium" | "high")
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Command catalog (lookup)
CREATE TABLE IF NOT EXISTS command_catalog (
    command_type TEXT PRIMARY KEY,
    description TEXT NOT NULL
);
-- Predicted passes (cached)
CREATE TABLE IF NOT EXISTS predicted_passes (
    pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
    gs_id INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    -- ('n2yo' | 'skyfield')
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gs_id) REFERENCES ground_stations(gs_id),
    FOREIGN KEY (s_id) REFERENCES satellites(s_id),
    CHECK (end_time > start_time)
);
-- Mission ↔ Satellite (many-to-many)
CREATE TABLE IF NOT EXISTS mission_satellites (
    mission_id INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_id, s_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id),
    FOREIGN KEY (s_id) REFERENCES satellites(s_id)
);
-- Reservations (references a predicted pass)
CREATE TABLE IF NOT EXISTS reservations (
    r_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    pass_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    -- (RESERVED | ACTIVE | COMPLETED | CANCELLED)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id),
    FOREIGN KEY (pass_id) REFERENCES predicted_passes(pass_id)
);
-- Commands scheduled within a reservation
CREATE TABLE IF NOT EXISTS reservation_commands (
    rc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    r_id INTEGER NOT NULL,
    command_type TEXT NOT NULL,
    execution_time TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    -- (PLANNED | QUEUED | SENT | ACKED | FAILED | CANCELLED)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (r_id) REFERENCES reservations(r_id),
    FOREIGN KEY (command_type) REFERENCES command_catalog(command_type)
);
-- Indexes to speed up next pass querying
CREATE INDEX IF NOT EXISTS idx_passes_by_station_time ON predicted_passes (gs_id, start_time);
CREATE INDEX IF NOT EXISTS idx_passes_by_sat_time ON predicted_passes (s_id, start_time);
-- Prevent adding repeat passes found/calculated
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_pass ON predicted_passes (s_id, gs_id, start_time, source);
-- Indexes to speed up 
CREATE INDEX IF NOT EXISTS idx_reservations_by_mission ON reservations (mission_id, created_at);
CREATE INDEX IF NOT EXISTS idx_commands_by_reservation_time ON reservation_commands (r_id, execution_time);

-- Enforce one reservation per pass
 CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_reservation_per_pass
 ON reservations (pass_id);
