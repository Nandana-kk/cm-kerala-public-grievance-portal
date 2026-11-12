"""
Database helper module using direct mysql-connector-python connections.
Provides simple, beginner-friendly helper functions with parameterized queries.
"""

import mysql.connector
from mysql.connector import Error
from config import Config


def get_db_connection(include_database=True):
    """
    Establish and return a new MySQL database connection.
    If include_database is False, connects to the MySQL server without selecting the database
    (useful during database creation / initialization).
    """
    connection_params = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
    }
    if include_database:
        connection_params["database"] = Config.DB_NAME

    try:
        connection = mysql.connector.connect(**connection_params)
        return connection
    except Error as e:
        print(f"[Database Connection Error] Could not connect to MySQL: {e}")
        raise e


def init_db(sql_filepath=None):
    """
    Initialize the MySQL database and tables by executing database.sql.
    """
    import os
    if sql_filepath is None:
        sql_filepath = os.path.join(os.path.dirname(__file__), "database.sql")

    # Connect to MySQL server without selecting database first
    conn = get_db_connection(include_database=False)
    cursor = conn.cursor()

    try:
        with open(sql_filepath, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Split script into individual SQL statements
        # Remove empty lines and comment lines
        statements = []
        current_stmt = []
        for line in sql_script.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            current_stmt.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current_stmt))
                current_stmt = []

        for statement in statements:
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        print("[Database Initialization] All tables created and initial data seeded successfully.")
    except Error as e:
        print(f"[Database Init Error] {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


def query_db(query, params=(), one=False):
    """
    Execute a SELECT query with parameterized inputs and return results as dictionaries.
    
    :param query: SQL string containing %s placeholders
    :param params: Tuple of parameters to safely inject
    :param one: If True, returns only the first row; otherwise returns a list of rows
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        records = cursor.fetchall()
        return (records[0] if records else None) if one else records
    finally:
        cursor.close()
        conn.close()


def execute_db(query, params=(), return_id=False):
    """
    Execute an INSERT, UPDATE, or DELETE query with parameterized inputs.
    
    :param query: SQL string containing %s placeholders
    :param params: Tuple of parameters to safely inject
    :param return_id: If True, returns cursor.lastrowid; otherwise returns cursor.rowcount
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        if return_id:
            return cursor.lastrowid
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()
