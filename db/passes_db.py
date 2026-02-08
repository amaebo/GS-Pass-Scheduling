from db.db_query import execute_row_id, execute_rowcount, fetch_one, fetch_all


def insert_predicted_pass_return_id(
    s_id: int,
    gs_id: int,
    max_elevation: float,
    duration: int,
    start_time: str,
    end_time: str,
    source: str,
) -> int | None:
    # IGNORE keyword in query handles duplicate entries by ignoring them.
    query = """
            INSERT OR IGNORE INTO predicted_passes (
                s_id,
                gs_id,
                max_elevation,
                duration,
                start_time,
                end_time,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    rowcount = execute_rowcount(
        query,
        (s_id, gs_id, max_elevation, duration, start_time, end_time, source),
    )
    if not rowcount:
        return None
    row = get_pass_id(gs_id, s_id, start_time, end_time)
    return row["pass_id"] if row else None


def insert_n2yo_pass_return_id(
    s_id: int,
    gs_id: int,
    max_elevation: float,
    duration: int,
    start_time: str,
    end_time: str,
) -> int | None:
    return insert_predicted_pass_return_id(
        s_id=s_id,
        gs_id=gs_id,
        max_elevation=max_elevation,
        duration=duration,
        start_time=start_time,
        end_time=end_time,
        source="n2yo",
    )


def get_latest_pass_end_time(gs_id: int, s_id: int):
    query = """
            SELECT end_time
            FROM predicted_passes
            WHERE gs_id = ? AND s_id = ?
            ORDER BY end_time DESC
            LIMIT 1
        """
    return fetch_one(query, (gs_id, s_id))


def get_claimable_passes(s_id:int, gs_id:int):
    #claimable passes are unreserved/non-cancelled, non‑expired passes
    query = """
            SELECT p.pass_id, p.gs_id, s.norad_id, p.start_time, p.end_time, p.source
            FROM predicted_passes as p
                INNER JOIN satellites as s ON p.s_id = s.s_id
            WHERE p.s_id = ? and p.gs_id = ?
              AND start_time >= CURRENT_TIMESTAMP
              AND NOT EXISTS (
                SELECT 1
                FROM reservations r
                WHERE r.pass_id = p.pass_id
                  AND r.cancelled_at IS NULL
              )
            ORDER BY start_time ASC
        """
    return fetch_all(query, (s_id, gs_id))

def delete_pass_by_pass_id(pass_id: int):
    query = """
            DELETE FROM predicted_passes
            WHERE pass_id = ?
        """
    return execute_rowcount(query, (pass_id,))

def delete_unreserved_expired_passes():
    query = """
            DELETE FROM predicted_passes
            WHERE end_time < CURRENT_TIMESTAMP
            AND NOT EXISTS (
                SELECT 1
                FROM reservations r
                WHERE r.pass_id = predicted_passes.pass_id
            );
        """
    return execute_rowcount(query)



def get_pass_id (gs_id: int, s_id: int, start_time: str, end_time: str):
    query = """
            SELECT pass_id
            FROM predicted_passes
            WHERE gs_id = ? and s_id = ? and start_time = ? and end_time = ?
        """
    return fetch_one(query, (gs_id, s_id, start_time, end_time))

def get_all_expired_passes():
    query = """
            SELECT *
            FROM predicted_passes
            WHERE start_time < CURRENT_TIMESTAMP
        """
    return fetch_all(query)


def get_pass_from_pass_id (pass_id: int):
    query = """
            SELECT *
            FROM predicted_passes
            WHERE pass_id = ?
        """
    return fetch_one(query,(pass_id,))

def pass_exists(pass_id: int) -> bool:
    query = """
            SELECT 1
            FROM predicted_passes
            WHERE pass_id = ?
        """
    return True if fetch_one(query, (pass_id,)) else False

def pass_is_future(pass_id: int) -> bool:
    query = """
            SELECT 1
            FROM predicted_passes
            WHERE pass_id = ?
              AND start_time > datetime('now', '+2 seconds')
        """
    return True if fetch_one(query, (pass_id,)) else False

def pass_has_active_reservation(pass_id: int) -> bool:
    query = """
            SELECT 1
            FROM reservations r
            WHERE r.pass_id = ?
              AND r.cancelled_at IS NULL
        """
    return True if fetch_one(query, (pass_id,)) else False
