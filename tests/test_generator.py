import sqlite3

from faker import Faker

from dummydatagen.generator import generate_row
from dummydatagen.schema import load_schema


def test_auto_pk_excluded_from_row(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    faker = Faker("en_US")
    row = generate_row(schema["users"], faker, {}, {})
    assert "id" not in row


def test_email_column_is_unique_and_valid(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    faker = Faker("en_US")
    unique_seen = {}
    seen_emails = set()
    for _ in range(5):
        row = generate_row(schema["users"], faker, {}, unique_seen)
        assert "@" in row["email"]
        assert row["email"] not in seen_emails
        seen_emails.add(row["email"])


def test_fk_value_drawn_from_pool(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    faker = Faker("en_US")
    fk_value_pools = {"users": [1, 2, 3]}
    row = generate_row(schema["posts"], faker, fk_value_pools, {})
    assert row["user_id"] in {1, 2, 3}
