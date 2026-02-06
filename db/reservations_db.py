from db.db_query import fetch_one, fetch_all, execute_rowcount
from db.db_init import db_connect

def get_all_reservations_with_details(include_cancelled: bool = False):
    if include_cancelled:
        query = """
            SELECT
                r.r_id,
                r.mission_id,
                r.pass_id,
                r.gs_id,
                s.norad_id,
                p.start_time,
                p.end_time,
                r.created_at,
                r.cancelled_at,
                CASE
                    WHEN r.cancelled_at IS NOT NULL THEN 'CANCELLED'
                    WHEN p.start_time > CURRENT_TIMESTAMP THEN 'RESERVED'
                    WHEN p.start_time <= CURRENT_TIMESTAMP AND p.end_time >= CURRENT_TIMESTAMP THEN 'ACTIVE'
                    WHEN p.end_time < CURRENT_TIMESTAMP THEN 'COMPLETE'
                    ELSE 'UNKNOWN'
                END AS status
            FROM reservations r
            JOIN predicted_passes p ON p.pass_id = r.pass_id
            JOIN satellites s ON s.s_id = r.s_id
            ORDER BY r.created_at DESC
        """
        return fetch_all(query)

    query = """
        SELECT
            r.r_id,
            r.mission_id,
            r.pass_id,
            r.gs_id,
            s.norad_id,
            p.start_time,
            p.end_time,
            r.created_at,
            r.cancelled_at,
            CASE
                WHEN r.cancelled_at IS NOT NULL THEN 'CANCELLED'
                WHEN p.start_time > CURRENT_TIMESTAMP THEN 'RESERVED'
                WHEN p.start_time <= CURRENT_TIMESTAMP AND p.end_time >= CURRENT_TIMESTAMP THEN 'ACTIVE'
                WHEN p.end_time < CURRENT_TIMESTAMP THEN 'COMPLETE'
                ELSE 'UNKNOWN'
            END AS status
        FROM reservations r
        JOIN predicted_passes p ON p.pass_id = r.pass_id
        JOIN satellites s ON s.s_id = r.s_id
        WHERE r.cancelled_at IS NULL
        ORDER BY r.created_at DESC
    """
    return fetch_all(query)


def get_reservation_with_details_by_r_id(r_id: int):
    query = """
        SELECT
            r.r_id,
            r.mission_id,
            r.pass_id,
            r.gs_id,
            s.norad_id,
            p.start_time,
            p.end_time,
            r.created_at,
            r.cancelled_at,
            CASE
                WHEN r.cancelled_at IS NOT NULL THEN 'CANCELLED'
                WHEN p.start_time > CURRENT_TIMESTAMP THEN 'RESERVED'
                WHEN p.start_time <= CURRENT_TIMESTAMP AND p.end_time >= CURRENT_TIMESTAMP THEN 'ACTIVE'
                WHEN p.end_time < CURRENT_TIMESTAMP THEN 'COMPLETE'
                ELSE 'UNKNOWN'
            END AS status,
            GROUP_CONCAT(rc.command_type) AS commands
        FROM reservations r
        JOIN predicted_passes p ON p.pass_id = r.pass_id
        JOIN satellites s ON s.s_id = r.s_id
        LEFT JOIN reservation_commands rc ON rc.r_id = r.r_id
        WHERE r.r_id = ?
        GROUP BY r.r_id
    """
    return fetch_one(query, (r_id,))


def get_reservation_commands_grouped():
    query = """
        SELECT r_id, GROUP_CONCAT(command_type) AS commands
        FROM reservation_commands
        GROUP BY r_id
    """
    return fetch_all(query)


def create_reservation_with_commands(
    pass_id: int,
    gs_id: int,
    s_id: int,
    mission_id: int | None,
    commands: list[str],
) -> int:
    conn = db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO reservations (mission_id, pass_id, gs_id, s_id)
            VALUES (?, ?, ?, ?)
            """,
            (mission_id, pass_id, gs_id, s_id),
        )
        r_id = cur.lastrowid

        for command in commands:
            conn.execute(
                """
                INSERT INTO reservation_commands (r_id, command_type)
                VALUES (?, ?)
                """,
                (r_id, command),
            )

        conn.commit()
        return r_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    

def get_reservations_with_details_by_mission_id(
    mission_id: int, include_cancelled: bool = False
):
    if include_cancelled:
        query = """
            SELECT
                r.r_id,
                r.mission_id,
                r.pass_id,
                r.gs_id,
                s.norad_id,
                p.start_time,
                p.end_time,
                r.created_at,
                r.cancelled_at,
                CASE
                    WHEN r.cancelled_at IS NOT NULL THEN 'CANCELLED'
                    WHEN p.start_time > CURRENT_TIMESTAMP THEN 'RESERVED'
                    WHEN p.start_time <= CURRENT_TIMESTAMP AND p.end_time >= CURRENT_TIMESTAMP THEN 'ACTIVE'
                    WHEN p.end_time < CURRENT_TIMESTAMP THEN 'COMPLETE'
                    ELSE 'UNKNOWN'
                END AS status
            FROM reservations r
            JOIN predicted_passes p ON p.pass_id = r.pass_id
            JOIN satellites s ON s.s_id = r.s_id
            WHERE r.mission_id = ?
            ORDER BY r.created_at DESC
        """
        return fetch_all(query, (mission_id,))

    query = """
        SELECT
            r.r_id,
            r.mission_id,
            r.pass_id,
            r.gs_id,
            s.norad_id,
            p.start_time,
            p.end_time,
            r.created_at,
            r.cancelled_at,
            CASE
                WHEN r.cancelled_at IS NOT NULL THEN 'CANCELLED'
                WHEN p.start_time > CURRENT_TIMESTAMP THEN 'RESERVED'
                WHEN p.start_time <= CURRENT_TIMESTAMP AND p.end_time >= CURRENT_TIMESTAMP THEN 'ACTIVE'
                WHEN p.end_time < CURRENT_TIMESTAMP THEN 'COMPLETE'
                ELSE 'UNKNOWN'
            END AS status
        FROM reservations r
        JOIN predicted_passes p ON p.pass_id = r.pass_id
        JOIN satellites s ON s.s_id = r.s_id
        WHERE r.mission_id = ?
          AND r.cancelled_at IS NULL
        ORDER BY r.created_at DESC
    """
    return fetch_all(query, (mission_id,))

def cancel_reservation_by_r_id(r_id: int):
    query = """
            UPDATE reservations
            SET cancelled_at = CURRENT_TIMESTAMP
            WHERE r_id = ?
        """
    return execute_rowcount(query, (r_id,))

def delete_cancelled_expired_passes():
    query = """
            DELETE FROM reservations
            WHERE cancelled_at IS NOT NULL
                AND r_id IN (SELECT r_id
                            FROM reservations
                            INNER JOIN predicted_passes ON reservations.pass_id= predicted_passes.pass_id
                            WHERE end_time < CURRENT_TIMESTAMP)
            """
    return execute_rowcount(query)

def delete_reservations_by_gs_id(gs_id:int):
    query = """
            DELETE FROM reservations
            WHERE gs_id = ?
             """
    return execute_rowcount(query,(gs_id,))