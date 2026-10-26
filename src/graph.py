"""Построение графа зависимостей: DFS без рекурсии."""

import sys


def filter_names(names, substring):
    """Убирает имена, содержащие подстроку (пустая подстрока: без фильтра)."""
    if not substring:
        return list(names)
    return [name for name in names if substring not in name]


def load_deps(package, get_deps, substring, is_root):
    """Получает зависимости пакета и применяет фильтр.

    Ошибка корневого пакета фатальна, у остальных она превращается
    в предупреждение, и пакет считается листом графа.
    """
    try:
        deps = get_deps(package)
    except ValueError as error:
        if is_root:
            raise
        print(f"Предупреждение: {package}: {error}", file=sys.stderr)
        deps = []
    return filter_names(deps, substring)


def build_graph(root, get_deps, max_depth, substring):
    """Строит граф {пакет: [зависимости]} обходом в глубину.

    Вместо рекурсии используется стек пар (пакет, глубина). Словарь
    expanded хранит наименьшую глубину, на которой пакет уже раскрыт:
    повторный заход на ту же или большую глубину пропускается, это
    обрывает циклы.
    """
    graph = {}
    expanded = {}
    cache = {}
    stack = [(root, 0)]
    while stack:
        package, depth = stack.pop()
        if package in expanded and depth >= expanded[package]:
            continue
        expanded[package] = depth
        if depth >= max_depth:
            graph.setdefault(package, [])
            continue
        if package not in cache:
            cache[package] = load_deps(
                package, get_deps, substring, package == root)
        graph[package] = cache[package]
        for dep in reversed(cache[package]):
            stack.append((dep, depth + 1))
    return graph