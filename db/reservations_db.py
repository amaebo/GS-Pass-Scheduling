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
    query = """
            SELECT command_type
            FROM reservation_commands
            WHERE r_id = ?
        """
    return fetch_all(query,(r_id,))
