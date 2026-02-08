PRAGMA foreign_keys = ON;
-- =========================
-- Ground stations
-- =========================
CREATE TABLE IF NOT EXISTS ground_stations (
    gs_id INTEGER PRIMARY KEY AUTOINCREMENT,
    gs_code TEXT NOT NULL UNIQUE,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    alt REAL NOT NULL,
    source TEXT NOT NULL,
    -- (MANUAL, AWS, SATNOGS etc.)
    status TEXT NOT NULL CHECK (status IN ("ACTIVE","INACTIVE")) ,
    -- (ACTIVE/INACTIVE)
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lat, lon)
);
-- =========================
-- Satellites
-- =========================
CREATE TABLE IF NOT EXISTS satellites (
    s_id INTEGER PRIMARY KEY AUTOINCREMENT,
    s_name TEXT NOT NULL,
    norad_id INTEGER NOT NULL UNIQUE,
    tle_line1 TEXT,
    tle_line2 TEXT,
    tle_updated_at TIMESTAMP,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- =========================
-- Missions
-- =========================
CREATE TABLE IF NOT EXISTS missions (
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_name TEXT NOT NULL,
    owner TEXT,
    priority TEXT,
    -- ("low" | "medium" | "high")
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- =========================
-- Mission ↔ Satellite (many-to-many)
-- =========================
CREATE TABLE IF NOT EXISTS mission_satellites (
    mission_id INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    role TEXT DEFAULT 'UNASSIGNED',
    -- 'PRIMARY'|'BACKUP'|'PAYLOAD'|'UNASSIGNED'
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_id, s_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (s_id) REFERENCES satellites(s_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-- =========================
-- Command catalog (lookup)
-- =========================
CREATE TABLE IF NOT EXISTS command_catalog (
    command_type TEXT PRIMARY KEY,
    description TEXT NOT NULL
);
-- =========================
-- Predicted passes (cached)
-- =========================
CREATE TABLE IF NOT EXISTS predicted_passes (
    pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
    gs_id INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    max_elevation REAL NOT NULL,
    duration INTEGER NOT NULL,
    source TEXT NOT NULL,
    -- ('n2yo'|'pyorbital')
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gs_id) REFERENCES ground_stations(gs_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (s_id) REFERENCES satellites(s_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK (end_time > start_time),
    UNIQUE (gs_id, s_id, start_time, end_time)
);
-- =========================
-- Reservations
-- Status and time window are derived by join to predicted_passes.
-- =========================
CREATE TABLE IF NOT EXISTS reservations (
    r_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER,
    -- NULL allowed
    pass_id INTEGER NOT NULL,
    gs_id INTEGER NOT NULL,
    s_id INTEGER NOT NULL,
    cancelled_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- Important: RESTRICT deletes of predicted_passes while referenced
    FOREIGN KEY (pass_id) REFERENCES predicted_passes(pass_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (gs_id) REFERENCES ground_stations(gs_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (s_id) REFERENCES satellites(s_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-- =========================
-- Commands scheduled within a reservation
-- =========================
CREATE TABLE IF NOT EXISTS reservation_commands (
    rc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    r_id INTEGER NOT NULL,
    command_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (r_id) REFERENCES reservations(r_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (command_type) REFERENCES command_catalog(command_type)
);
-- =========================
-- Indexes
-- =========================
-- Pass prediction queries
CREATE INDEX IF NOT EXISTS idx_passes_by_gs_sat_start ON predicted_passes (gs_id, s_id, start_time);
-- Reservation queries
CREATE INDEX IF NOT EXISTS idx_reservations_by_mission ON reservations (mission_id, created_at);
-- Fast lookup / joins by pass_id
CREATE INDEX IF NOT EXISTS idx_reservations_by_pass ON reservations (pass_id);
-- Optional filtering support (you still have gs_id/s_id on reservations)
CREATE INDEX IF NOT EXISTS idx_reservations_by_gs ON reservations (gs_id, created_at);
CREATE INDEX IF NOT EXISTS idx_reservations_by_sat ON reservations (s_id, created_at);
-- Reservation command scheduling queries
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_command_per_reservation ON reservation_commands (r_id, command_type);
-- Enforce one ACTIVE reservation per pass (cancelled reservations don't block)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_reservation_per_pass ON reservations (pass_id)
WHERE cancelled_at IS NULL;
