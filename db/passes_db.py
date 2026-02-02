from db.db_query import execute_row_id
def add_new_passes_from_n2yo(s_id: int, gs_id:int, start_time: str, end_time: str):
     # IGNORE keyword in query handles duplicate entries by ignoring them.
    query = """
            INSERT OR IGNORE INTO predicted_passes (s_id, gs_id, start_time, end_time, source)
            VALUES (?, ?, ?, ?, N2YO)  
        """
    return execute_row_id(query, (s_id, gs_id, start_time, end_time))