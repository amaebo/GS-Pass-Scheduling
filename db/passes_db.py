from db.db_query import execute_row_id, execute_rowcount, fetch_one, fetch_all
def add_new_passes_from_n2yo(s_id: int, gs_id:int, start_time: str, end_time: str):
     # IGNORE keyword in query handles duplicate entries by ignoring them.
    query = """
            INSERT OR IGNORE INTO predicted_passes (s_id, gs_id, start_time, end_time, source)
            VALUES (?, ?, ?, ?, N2YO)  
        """
    return execute_row_id(query, (s_id, gs_id, start_time, end_time))

def get_passes_by_gs_and_sat(s_id:int, gs_id:int):
    query = """
            SELECT *
            FROM pass_predictions
            WHERE s_id = ? and gs_id = ?
        """
    return fetch_all(query, (s_id, gs_id))
    
def delete_pass_by_pass_id(pass_id: int):
    query = """
            DELETE FROM pass_predictions
            WHERE pass_id = ?
        """
    return execute_rowcount(query, (pass_id,))

def delete_expired_passes():
    query = """
            DELETE FROM pass_predictions
            WHERE start_time < CURRENT_TIMESTAMP
        """
    return execute_rowcount(query)

def get_pass_id (gs_id: int, s_id: int, start_time: str, end_time: str):
    query = """
            SELECT pass_id
            FROM pass_predictions
            WHERE gs_id = ? and s_id = ? and start_time = ? and end_time = ?
        """
    return fetch_one(query, (gs_id, s_id, start_time, end_time))

def get_all_expired_passes():
    query = """
            SELECT *
            FROM pass_predictions
            WHERE start_time < CURRENT_TIMESTAMP
        """
    return fetch_all(query)