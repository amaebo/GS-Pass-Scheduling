PRAGMA foreign_keys = ON;
-- =========================================================
-- DEV RESET (child tables first)
-- =========================================================
DELETE FROM reservation_commands;
DELETE FROM reservations;
DELETE FROM mission_satellites;
DELETE FROM predicted_passes;
DELETE FROM command_catalog;
DELETE FROM missions;
DELETE FROM satellites;
DELETE FROM ground_stations;
-- =========================================================
-- Ground stations
-- =========================================================
INSERT INTO ground_stations (
        gs_id,
        gs_code,
        lat,
        lon,
        alt,
        source,
        status,
        date_added
    )
VALUES (
        1,
        'DEN_CO',
        39.7392,
        -104.9903,
        1609.0,
        'MANUAL',
        'ACTIVE',
        '2026-01-10 12:00:00'
    ),
    (
        2,
        'BOU_CO',
        40.01499,
        -105.27055,
        1655.0,
        'MANUAL',
        'ACTIVE',
        '2026-01-10 12:05:00'
    ),
    (
        3,
        'SFO_CA',
        37.7749,
        -122.4194,
        16.0,
        'MANUAL',
        'ACTIVE',
        '2026-01-10 12:10:00'
    );
-- =========================================================
-- Satellites
-- Notes:
-- - TLE lines are sample-format, not guaranteed current/valid.
-- - mode: SAFE | NOMINAL | PAYLOAD
-- - health_status: OK | DEGRADED | UNKNOWN
-- =========================================================
INSERT INTO satellites (
        s_id,
        s_name,
        norad_id,
        tle_line1,
        tle_line2,
        tle_updated_at,
        mode,
        health_status,
        last_contact_time,
        date_added
    )
VALUES (
        1,
        'ISS (ZARYA)',
        25544,
        '1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991',
        '2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10',
        '2026-01-29 18:00:00',
        'NOMINAL',
        'OK',
        '2026-01-29 18:10:00',
        '2026-01-10 12:10:00'
    ),
    (
        2,
        'AQUA',
        27424,
        '1 27424U 02022A   26029.40000000  .00002000  00000-0  12000-3 0  9996',
        '2 27424  98.2000  40.0000 0001000  10.0000  80.0000 14.57000000    20',
        '2026-01-29 18:05:00',
        'PAYLOAD',
        'OK',
        '2026-01-28 22:30:00',
        '2026-01-10 12:15:00'
    ),
    (
        3,
        'NOAA 15',
        25338,
        '1 25338U 98030A   26029.30000000  .00001000  00000-0  90000-4 0  9992',
        '2 25338  98.7000 200.0000 0010000  90.0000 270.0000 14.26000000    30',
        '2026-01-29 18:08:00',
        'SAFE',
        'DEGRADED',
        '2026-01-25 05:00:00',
        '2026-01-10 12:20:00'
    );
-- =========================================================
-- Missions
-- priority: "low" | "medium" | "high"
-- =========================================================
INSERT INTO missions (
        mission_id,
        mission_name,
        owner,
        priority,
        date_added
    )
VALUES (
        1,
        'ISS Ops Demo',
        'Ama',
        'medium',
        '2026-01-11 09:00:00'
    ),
    (
        2,
        'Earth Observation Testbed',
        'CU Denver',
        'high',
        '2026-01-11 09:10:00'
    );
-- =========================================================
-- Mission ↔ Satellite links
-- role examples: PRIMARY | SECONDARY | PAYLOAD
-- =========================================================
INSERT INTO mission_satellites (mission_id, s_id, role, date_added)
VALUES (1, 1, 'PRIMARY', '2026-01-11 09:30:00'),
    (2, 2, 'PAYLOAD', '2026-01-11 09:35:00'),
    (2, 3, 'SECONDARY', '2026-01-11 09:36:00');
-- =========================================================
-- Command catalog
-- =========================================================
INSERT INTO command_catalog (command_type, description)
VALUES ('PING', 'Basic connectivity check'),
    ('GET_TELEMETRY', 'Request a telemetry snapshot'),
    ('SET_MODE_SAFE', 'Set satellite mode to SAFE'),
    (
        'SET_MODE_NOMINAL',
        'Set satellite mode to NOMINAL'
    ),
    ('START_PAYLOAD', 'Start payload operations'),
    ('STOP_PAYLOAD', 'Stop payload operations'),
    ('DOWNLINK', 'Request/trigger downlink operation');
-- =========================================================
-- Predicted passes (cached)
-- source: 'n2yo' | 'skyfield'
-- CHECK(end_time > start_time) enforced
-- UNIQUE(s_id, gs_id, start_time, source) enforced
-- =========================================================
INSERT INTO predicted_passes (
        pass_id,
        gs_id,
        s_id,
        start_time,
        end_time,
        max_elevation,
        duration,
        source,
        created_at
    )
VALUES -- ISS over DEN
    (
        1,
        1,
        1,
        '2026-01-30 13:02:00',
        '2026-01-30 13:10:30',
        62.4,
        510,
        'n2yo',
        '2026-01-29 19:00:00'
    ),
    (
        2,
        1,
        1,
        '2026-01-31 01:22:10',
        '2026-01-31 01:29:40',
        28.1,
        450,
        'skyfield',
        '2026-01-29 19:00:00'
    ),
    -- AQUA over BOU
    (
        3,
        2,
        2,
        '2026-01-30 15:40:00',
        '2026-01-30 15:46:20',
        17.9,
        380,
        'n2yo',
        '2026-01-29 19:02:00'
    ),
    (
        4,
        2,
        2,
        '2026-02-01 04:18:00',
        '2026-02-01 04:27:00',
        55.2,
        540,
        'skyfield',
        '2026-01-29 19:02:00'
    ),
    -- NOAA 15 over DEN
    (
        5,
        1,
        3,
        '2026-01-30 22:05:30',
        '2026-01-30 22:14:10',
        44.7,
        520,
        'n2yo',
        '2026-01-29 19:05:00'
    ),
    (
        6,
        1,
        3,
        '2026-02-02 12:11:00',
        '2026-02-02 12:19:30',
        79.6,
        510,
        'skyfield',
        '2026-01-29 19:05:00'
    );
-- =========================================================
-- Reservations (source of truth)
-- - pass_id kept for traceability
-- - one ACTIVE reservation per pass_id enforced by partial unique index
--   (cancelled_at IS NULL)
-- =========================================================
INSERT INTO reservations (
        r_id,
        mission_id,
        pass_id,
        gs_id,
        s_id,
        cancelled_at,
        created_at,
        updated_at
    )
VALUES -- Active reservation for ISS pass 1, tied to mission 1
    (
        1,
        1,
        1,
        1,
        1,
        NULL,
        '2026-01-29 19:10:00',
        '2026-01-29 19:15:00'
    ),
    -- Cancelled reservation for NOAA pass 5 (lets you test cancellation behavior)
    (
        2,
        2,
        5,
        1,
        3,
        '2026-01-29 20:00:00',
        '2026-01-29 19:20:00',
        '2026-01-29 20:00:00'
    ),
    -- Active reservation for AQUA pass 4, tied to mission 2
    (
        3,
        2,
        4,
        2,
        2,
        NULL,
        '2026-01-29 19:25:00',
        '2026-01-29 19:30:00'
    );
-- =========================================================
-- Commands scheduled within a reservation
-- status: PLANNED | QUEUED | SENT | ACKED | FAILED | CANCELLED
-- =========================================================
INSERT INTO reservation_commands (
        rc_id,
        r_id,
        command_type,
        created_at
)
VALUES -- Reservation 1 (ISS) - normal flow
    (
        1,
        1,
        'PING',
        '2026-01-29 19:12:00'
    ),
    (
        2,
        1,
        'GET_TELEMETRY',
        '2026-01-29 19:12:30'
    ),
    (
        3,
        1,
        'SET_MODE_SAFE',
        '2026-01-29 19:13:00'
    ),
    -- Reservation 2 (NOAA) was cancelled, so commands are cancelled too
    (
        4,
        2,
        'PING',
        '2026-01-29 19:22:00'
    ),
    (
        5,
        2,
        'GET_TELEMETRY',
        '2026-01-29 19:22:30'
    ),
    -- Reservation 3 (AQUA) - some progress statuses
    (
        6,
        3,
        'START_PAYLOAD',
        '2026-01-29 19:26:00'
    ),
    (
        7,
        3,
        'DOWNLINK',
        '2026-01-29 19:26:30'
    );
