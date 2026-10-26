"""Тесты разбора файла тестового репозитория."""

import os
import tempfile
import unittest

from testrepo import read_test_repo


class TestRepoTest(unittest.TestCase):
    """Проверка формата файла 'A: B C'."""

    def setUp(self):
        """Создаёт временную папку."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def read(self, text):
        """Записывает текст в файл и разбирает его."""
        path = os.path.join(self.tmp.name, "repo.txt")
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return read_test_repo(path)

    def test_valid(self):
        """Корректный файл читается, комментарии пропускаются."""
        graph = self.read("# коммент\nA: B C\nB:\n\n")
        self.assertEqual(graph, {"A": ["B", "C"], "B": []})

    def test_errors(self):
        """Некорректные файлы дают ValueError."""
        for text in ["A B C\n", "A: b\n", "a: B\n", "A: B\nA: C\n",
                     "A: B: C\n"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    self.read(text)


if __name__ == "__main__":
    unittest.main()