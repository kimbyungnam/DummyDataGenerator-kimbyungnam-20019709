import sqlite3

import pytest

from dummydatagen.errors import CycleError
from dummydatagen.graph import build_dependency_graph, topological_order
from dummydatagen.schema import load_schema


def test_topological_order(sample_db):
    conn = sqlite3.connect(sample_db)
    schema = load_schema(conn)
    graph = build_dependency_graph(schema)
    order = topological_order(graph)
    assert order.index("users") < order.index("posts")
    assert order.index("posts") < order.index("comments")


def test_cycle_detection(cyclic_db):
    conn = sqlite3.connect(cyclic_db)
    schema = load_schema(conn)
    graph = build_dependency_graph(schema)
    with pytest.raises(CycleError):
        topological_order(graph)
