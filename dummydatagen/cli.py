import argparse
import os
import random
import sqlite3
import sys

from faker import Faker

from .errors import CycleError, DummyDataGenError
from .generator import generate_row
from .graph import build_dependency_graph, topological_order
from .inserter import insert_row
from .schema import load_schema


def parse_rows_spec(spec):
    """'100' -> 100 (int, default for every table). 'users=50,posts=10' -> dict."""
    if "=" not in spec:
        return int(spec)
    result = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        table, _, count = part.partition("=")
        result[table.strip()] = int(count.strip())
    return result


def rows_for_table(rows_spec, table_name):
    if isinstance(rows_spec, int):
        return rows_spec
    return rows_spec.get(table_name, 0)


def print_schema(schema):
    for name, table in schema.items():
        print(f"{name}")
        for col in table.columns:
            markers = []
            if col.is_pk:
                markers.append("PK")
            if col.not_null:
                markers.append("NOT NULL")
            if col.name in table.unique_columns:
                markers.append("UNIQUE")
            suffix = f" ({', '.join(markers)})" if markers else ""
            print(f"  {col.name}: {col.decl_type or col.affinity}{suffix}")
        for fk in table.foreign_keys:
            print(f"  FK: {fk.from_column} -> {fk.to_table}.{fk.to_column}")


def process_table(conn, table, count, faker, fk_value_pools, unique_seen, dry_run):
    pool = fk_value_pools.setdefault(table.name, [])
    for _ in range(count):
        row = generate_row(table, faker, fk_value_pools, unique_seen)
        pk_value = insert_row(conn, table, row, dry_run=dry_run)
        if pk_value is not None:
            pool.append(pk_value)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="dummydatagen",
        description="Generate dummy data for a SQLite database based on its existing schema.",
    )
    parser.add_argument("--db", required=True, help="Path to the SQLite database file")
    parser.add_argument(
        "--rows",
        default="10",
        help="Row count per table: a single number (default for all tables) "
        "or 'table1=N,table2=M'",
    )
    parser.add_argument("--tables", help="Comma-separated list of tables to populate (default: all)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible output")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL instead of executing it")
    parser.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")
    parser.add_argument("--list-tables", action="store_true", help="Print schema and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    if not os.path.exists(args.db):
        print(f"Error: database file not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        schema = load_schema(conn)

        if args.list_tables:
            print_schema(schema)
            return 0

        if not schema:
            print("No tables found in database.", file=sys.stderr)
            return 1

        graph = build_dependency_graph(schema)
        try:
            order = topological_order(graph)
        except CycleError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        if args.seed is not None:
            random.seed(args.seed)
            Faker.seed(args.seed)
        faker = Faker(args.locale)

        rows_spec = parse_rows_spec(args.rows)
        target_tables = set(args.tables.split(",")) if args.tables else set(order)

        fk_value_pools = {}
        unique_seen = {}

        conn.execute("BEGIN")
        try:
            for table_name in order:
                count = rows_for_table(rows_spec, table_name) if table_name in target_tables else 0
                if args.verbose:
                    print(f"Populating {table_name}: {count} rows", file=sys.stderr)
                process_table(
                    conn,
                    schema[table_name],
                    count,
                    faker,
                    fk_value_pools,
                    unique_seen,
                    args.dry_run,
                )
            if args.dry_run:
                conn.rollback()
            else:
                conn.commit()
        except DummyDataGenError as e:
            conn.rollback()
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
