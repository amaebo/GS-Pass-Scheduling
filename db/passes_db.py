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

def get_passes_by_gs_and_sat(s_id:int, gs_id:int):
    query = """
            SELECT *
            FROM predicted_passes
            WHERE s_id = ? and gs_id = ?
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
