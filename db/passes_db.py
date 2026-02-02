from db.db_query import execute_row_id, execute_rowcount, fetch_one, fetch_all


def insert_n2yo_pass_return_id(
    s_id: int,
    gs_id: int,
    start_time: str,
    end_time: str,
) -> int | None:
    # IGNORE keyword in query handles duplicate entries by ignoring them.
    query = """
            INSERT OR IGNORE INTO predicted_passes (s_id, gs_id, start_time, end_time, source)
            VALUES (?, ?, ?, ?, ?)  
        """
    rowcount = execute_rowcount(query, (s_id, gs_id, start_time, end_time, "n2yo"))
    if not rowcount:
        return None
    row = get_pass_id(gs_id, s_id, start_time, end_time)
    return row["pass_id"] if row else None


def get_latest_pass_end_time(gs_id: int, s_id: int):
    query = """
            SELECT end_time
            FROM predicted_passes
            WHERE gs_id = ? AND s_id = ?
            ORDER BY end_time DESC
            LIMIT 1
        """
    return fetch_one(query, (gs_id, s_id))


def get_all_future_passes(s_id:int, gs_id:int):
    query = """
            SELECT p.pass_id, p.gs_id, s.norad_id, p.start_time, p.end_time, p.source
            FROM predicted_passes as p
                INNER JOIN satellites as s ON p.s_id = s.s_id
            WHERE p.s_id = ? and p.gs_id = ?
              AND start_time >= CURRENT_TIMESTAMP
            ORDER BY start_time ASC
        """
    return fetch_all(query, (s_id, gs_id))

def delete_pass_by_pass_id(pass_id: int):
    query = """
            DELETE FROM predicted_passes
            WHERE pass_id = ?
        """
    return execute_rowcount(query, (pass_id,))

def delete_expired_passes():
    query = """
            DELETE FROM predicted_passes
            WHERE start_time < CURRENT_TIMESTAMP
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
