from db.db_query import execute_row_id

def insert_reservation(pass_id: int, gs_id: int, s_id: int, mission_id: int | None ):
    query = """
            INSERT INTO reservations (mission_id, pass_id, gs_id, s_id)
            VALUES (?, ?, ?, ?)
        """
    return execute_row_id(query, (mission_id, pass_id, gs_id, s_id))
    

def add_command_to_reservation(r_id: int, command: list[str] | None):
    query = """
            INSERT INTO reservation_commands (r_id, command_type)
            VALUES (?, ?)
        """
    return execute_row_id(query,(r_id, command))