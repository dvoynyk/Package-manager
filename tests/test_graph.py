"""Тесты построения графа и вывода дерева."""

import contextlib
import io
import os
import unittest

from graph import build_graph
from output import render_list, render_tree
from testrepo import read_test_repo

DATA = os.path.join(os.path.dirname(__file__), "data", "repo.txt")


def make_getter():
    """Создаёт функцию зависимостей по тестовому файлу."""
    repo = read_test_repo(DATA)
    return lambda name: repo.get(name, [])


class GraphTest(unittest.TestCase):
    """Проверка DFS, глубины, фильтра и циклов."""

    def tree(self, root, depth, substring=""):
        """Строит граф и возвращает строки дерева."""
        graph = build_graph(root, make_getter(), depth, substring)
        return render_tree(graph, root, depth)

    def test_graph_structure(self):
        """Граф содержит все пакеты и их прямые зависимости."""
        graph = build_graph("A", make_getter(), 5, "")
        expected = {"A": ["B", "C"], "B": ["D"], "C": ["D", "E"],
                    "D": [], "E": []}
        self.assertEqual(graph, expected)

    def test_full_tree(self):
        """Общая зависимость D показана под обоими родителями."""
        expected = ["A", "├── B", "│   └── D", "└── C",
                    "    ├── D", "    └── E"]
        self.assertEqual(self.tree("A", 5), expected)

    def test_depth_one(self):
        """При глубине 1 видны только прямые зависимости."""
        self.assertEqual(self.tree("A", 1), ["A", "├── B", "└── C"])

    def test_depth_zero(self):
        """При глубине 0 остаётся только корень."""
        self.assertEqual(self.tree("A", 0), ["A"])

    def test_filter(self):
        """Пакет с подстрокой в имени исключается из графа."""
        expected = ["A", "├── B", "└── C", "    └── E"]
        self.assertEqual(self.tree("A", 5, "D"), expected)

    def test_cycle(self):
        """Цикл X -> Y -> Z -> X обрывается пометкой."""
        expected = ["X", "└── Y", "    └── Z", "        └── X (цикл)"]
        self.assertEqual(self.tree("X", 10), expected)

    def test_self_dependency(self):
        """Пакет, зависящий от самого себя, не зацикливает обход."""
        expected = ["S", "├── S (цикл)", "└── T"]
        self.assertEqual(self.tree("S", 10), expected)

    def test_list_mode(self):
        """Режим списка выводит по строке на пакет."""
        graph = build_graph("A", make_getter(), 5, "")
        lines = render_list(graph)
        self.assertEqual(lines[0], "A -> B, C")
        self.assertIn("D -> (нет зависимостей)", lines)

    def test_root_error_is_fatal(self):
        """Ошибка получения зависимостей корня пробрасывается."""
        def broken(name):
            """Всегда падает."""
            raise ValueError("сбой")

        with self.assertRaises(ValueError):
            build_graph("A", broken, 3, "")

    def test_nested_error_is_warning(self):
        """Ошибка вложенного пакета превращается в предупреждение."""
        def getter(name):
            """Падает только на пакете B."""
            if name == "B":
                raise ValueError("сбой")
            return ["B"] if name == "A" else []

        with contextlib.redirect_stderr(io.StringIO()):
            graph = build_graph("A", getter, 3, "")
        self.assertEqual(graph, {"A": ["B"], "B": []})


if __name__ == "__main__":
    unittest.main()