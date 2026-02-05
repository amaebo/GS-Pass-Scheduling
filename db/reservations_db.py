from db.db_query import execute_row_id, fetch_one, fetch_all

def insert_reservation(pass_id: int, gs_id: int, s_id: int, mission_id: int | None ):
    query = """
            INSERT INTO reservations (mission_id, pass_id, gs_id, s_id)
            VALUES (?, ?, ?, ?)
        """
    return execute_row_id(query, (mission_id, pass_id, gs_id, s_id))
    

def add_command_to_reservation(r_id: int, command: str):
    query = """
            INSERT INTO reservation_commands (r_id, command_type)
            VALUES (?, ?)
        """
    return execute_row_id(query, (r_id, command))

def get_reservation_by_r_id(r_id: int):
    query = """
            SELECT *
            FROM reservations 
            WHERE r_id = ?
        """
    return fetch_one(query,(r_id,))

def get_reservation_commands_by_r_id(r_id:int):
    query = """
            SELECT command_type
            FROM reservation_commands
            WHERE r_id = ?
        """
    return fetch_all(query,(r_id,))
