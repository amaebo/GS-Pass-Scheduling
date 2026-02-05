from db.db_query import fetch_all

def get_all_commands():
    query = """
            SELECT *
            FROM command_catalog
        """
    return fetch_all(query)