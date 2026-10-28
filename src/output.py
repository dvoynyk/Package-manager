"""Форматирование графа: ASCII-дерево и простой список."""

TEE = "├── "
CORNER = "└── "
PIPE = "│   "
BLANK = "    "


def push_children(stack, graph, node, prefix, path):
    """Кладёт потомков узла в стек так, чтобы первый вышел первым."""
    kids = graph.get(node, [])
    marks = [TEE] * len(kids)
    if marks:
        marks[-1] = CORNER
    for kid, mark in reversed(list(zip(kids, marks))):
        stack.append((kid, mark, prefix, path))


def render_tree(graph, root, max_depth):
    """Возвращает строки ASCII-дерева (обход тоже без рекурсии).

    Глубина узла равна длине пути от корня. Узел, уже стоящий среди
    своих предков, выводится с пометкой '(цикл)' и не раскрывается.
    """
    lines = [root]
    stack = []
    push_children(stack, graph, root, "", (root,))
    while stack:
        node, mark, prefix, path = stack.pop()
        if node in path:
            lines.append(f"{prefix}{mark}{node} (цикл)")
            continue
        lines.append(f"{prefix}{mark}{node}")
        if len(path) < max_depth:
            shift = BLANK if mark == CORNER else PIPE
            push_children(stack, graph, node, prefix + shift,
                          path + (node,))
    return lines


def render_list(graph):
    lines = []
    for package, deps in graph.items():
        text = ", ".join(deps) if deps else "(нет зависимостей)"
        lines.append(f"{package} -> {text}")
    edges = sum(len(deps) for deps in graph.values())
    lines.append(f"Вершин: {len(graph)}, рёбер: {edges}")
    return lines