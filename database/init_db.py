"""
database/init_db.py
-------------------
Creates the database and tables on first run.
Run this once before anything else.
"""

import sqlite3
import os
from loguru import logger
from config.settings import DB_PATH
from database.models import CREATE_MEMBERS_TABLE, CREATE_ATTENDANCE_TABLE


def init_db() -> sqlite3.Connection:
    """
    Creates the database file and tables if they don't exist.
    Returns an open connection.
    """
    # Make sure the database folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # lets us access columns by name, not index
    cur = conn.cursor()

    cur.execute(CREATE_MEMBERS_TABLE)
    cur.execute(CREATE_ATTENDANCE_TABLE)
    conn.commit()

    logger.info(f"Database ready at: {DB_PATH}")
    return conn


if __name__ == "__main__":
    init_db()
    logger.info("Done.")