"""
database/models.py
------------------
SQL table definitions for Facemark.
These are the exact tables that will be created in the database.
"""

CREATE_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS members (
    member_id       TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    group_label     TEXT,
    photo_path      TEXT,
    registered_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ATTENDANCE_TABLE = """
CREATE TABLE IF NOT EXISTS attendance (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       TEXT NOT NULL,
    date            DATE NOT NULL,
    time_in         TIME NOT NULL,
    method          TEXT DEFAULT 'face',
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    UNIQUE(member_id, date)
);
"""