from collections import deque

from .errors import CycleError


def build_dependency_graph(schema):
    """Return {table: set(tables it depends on)}, excluding self-referencing FKs."""
    graph = {name: set() for name in schema}
    for name, table in schema.items():
        for fk in table.foreign_keys:
            if fk.to_table != name and fk.to_table in graph:
                graph[name].add(fk.to_table)
    return graph


def topological_order(graph):
    """Kahn's algorithm. Returns tables ordered parents-first. Raises CycleError on a cycle."""
    in_degree = {node: 0 for node in graph}
    dependents = {node: [] for node in graph}
    for node, deps in graph.items():
        in_degree[node] = len(deps)
        for dep in deps:
            dependents[dep].append(node)

    queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for dependent in sorted(dependents[node]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(graph):
        remaining = [n for n in graph if n not in order]
        raise CycleError(remaining)
    return order
