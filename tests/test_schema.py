import sqlite3

from dummydatagen.schema import load_schema


def test_load_schema_tables(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    assert set(schema.keys()) == {"users", "posts", "comments"}


def test_columns_and_pk(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    users = schema["users"]
    id_col = next(c for c in users.columns if c.name == "id")
    assert id_col.is_pk
    assert id_col.affinity == "INTEGER"
    assert users.single_integer_pk().name == "id"

    email_col = next(c for c in users.columns if c.name == "email")
    assert email_col.not_null
    assert "email" in users.unique_columns


def test_foreign_keys(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    posts = schema["posts"]
    assert len(posts.foreign_keys) == 1
    fk = posts.foreign_keys[0]
    assert fk.from_column == "user_id"
    assert fk.to_table == "users"
    assert fk.to_column == "id"
