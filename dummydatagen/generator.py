import random
import re
import uuid

from faker import Faker

from .errors import EmptyFKPoolError, UniqueRetryExceeded

_UNIQUE_MAX_ATTEMPTS = 1000

NAME_PATTERNS = [
    (re.compile(r"email"), lambda f: f.unique.email()),
    (re.compile(r"first_?name"), lambda f: f.first_name()),
    (re.compile(r"last_?name"), lambda f: f.last_name()),
    (re.compile(r"\bname\b"), lambda f: f.name()),
    (re.compile(r"phone"), lambda f: f.phone_number()),
    (re.compile(r"address|street"), lambda f: f.address()),
    (re.compile(r"city"), lambda f: f.city()),
    (re.compile(r"country"), lambda f: f.country()),
    (re.compile(r"zip|postal"), lambda f: f.postcode()),
    (re.compile(r"url|website"), lambda f: f.url()),
    (re.compile(r"created_at|updated_at|_at$|timestamp"), lambda f: f.date_time_this_decade().isoformat(sep=" ")),
    (re.compile(r"date"), lambda f: f.date()),
    (re.compile(r"^is_|_flag$|active"), lambda f: f.pyint(0, 1)),
    (re.compile(r"price|amount|salary|cost"), lambda f: str(f.pydecimal(left_digits=4, right_digits=2, positive=True))),
    (re.compile(r"description|comment|body|content"), lambda f: f.text(max_nb_chars=200)),
    (re.compile(r"title"), lambda f: f.sentence(nb_words=6)),
    (re.compile(r"username"), lambda f: f.unique.user_name()),
    (re.compile(r"uuid|guid"), lambda f: str(uuid.uuid4())),
]

FALLBACK_BY_AFFINITY = {
    "INTEGER": lambda f: f.pyint(1, 100000),
    "REAL": lambda f: f.pyfloat(left_digits=3, right_digits=2),
    "TEXT": lambda f: f.word(),
    "BLOB": lambda f: f.binary(length=16),
    "NUMERIC": lambda f: str(f.pydecimal(left_digits=5, right_digits=2)),
}


def value_for_column(col, faker):
    name_lower = col.name.lower()
    for pattern, fn in NAME_PATTERNS:
        if pattern.search(name_lower):
            return fn(faker)
    return FALLBACK_BY_AFFINITY.get(col.affinity, FALLBACK_BY_AFFINITY["TEXT"])(faker)


def _unique_value(table_name, col, faker, unique_seen):
    key = (table_name, col.name)
    seen = unique_seen.setdefault(key, set())
    for _ in range(_UNIQUE_MAX_ATTEMPTS):
        value = value_for_column(col, faker)
        if value not in seen:
            seen.add(value)
            return value
    raise UniqueRetryExceeded(table_name, col.name, _UNIQUE_MAX_ATTEMPTS)


def generate_row(table, faker, fk_value_pools, unique_seen):
    """Build one row as {column_name: value}, skipping auto-increment integer PKs."""
    auto_pk = table.single_integer_pk()
    fk_by_column = {fk.from_column: fk for fk in table.foreign_keys}

    row = {}
    for col in table.columns:
        if auto_pk is not None and col.name == auto_pk.name:
            continue

        fk = fk_by_column.get(col.name)
        if fk is not None:
            pool = fk_value_pools.get(fk.to_table) or []
            if not pool:
                if fk.to_table == table.name and not col.not_null:
                    row[col.name] = None
                    continue
                raise EmptyFKPoolError(table.name, col.name, fk.to_table)
            row[col.name] = random.choice(pool)
            continue

        if col.name in table.unique_columns:
            row[col.name] = _unique_value(table.name, col, faker, unique_seen)
        else:
            row[col.name] = value_for_column(col, faker)

    return row


def make_faker(locale="en_US"):
    return Faker(locale)
