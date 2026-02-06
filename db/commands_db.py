from db.db_query import fetch_all

def get_all_commands():
    query = """
            SELECT *
            FROM command_catalog
        """
    return fetch_all(query)


def get_command_types() -> set[str]:
    query = """
            SELECT command_type
            FROM command_catalog
        """
    rows = fetch_all(query)
    return {row["command_type"] for row in rows} if rows else set()
