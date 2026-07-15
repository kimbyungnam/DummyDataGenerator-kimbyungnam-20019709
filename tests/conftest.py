import sqlite3

import pytest


@pytest.fixture
def sample_db(tmp_path):
    db_path = tmp_path / "sample.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            body TEXT
        );
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id),
            author_email TEXT,
            comment TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def cyclic_db(tmp_path):
    db_path = tmp_path / "cyclic.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE a (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            b_id INTEGER REFERENCES b(id)
        );
        CREATE TABLE b (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            a_id INTEGER REFERENCES a(id)
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path
