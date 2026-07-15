import sqlite3

from dummydatagen.cli import main


def test_populates_tables_respecting_fk_integrity(sample_db):
    exit_code = main(
        [
            "--db",
            str(sample_db),
            "--rows",
            "users=5,posts=10,comments=20",
            "--seed",
            "1",
        ]
    )
    assert exit_code == 0

    conn = sqlite3.connect(sample_db)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 10
    assert conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0] == 20

    conn.execute("PRAGMA foreign_keys = ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == []


def test_dry_run_does_not_insert(sample_db):
    exit_code = main(["--db", str(sample_db), "--rows", "users=3", "--dry-run"])
    assert exit_code == 0

    conn = sqlite3.connect(sample_db)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_list_tables(sample_db, capsys):
    exit_code = main(["--db", str(sample_db), "--list-tables"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "users" in out
    assert "posts" in out
