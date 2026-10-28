"""Тесты чтения и проверки конфигурации."""

import csv
import os
import shutil
import tempfile
import unittest

from config import load_config

REPO = os.path.join(os.path.dirname(__file__), "data", "repo.txt")
BASE = {
    "package_name": "A",
    "repository": "https://api.nuget.org/v3/index.json",
    "test_mode": "false",
    "ascii_tree": "true",
    "max_depth": "3",
    "filter_substring": "",
}


class ConfigTest(unittest.TestCase):
    """Проверка загрузки конфигурации и сообщений об ошибках."""

    def folder(self):
        """Создаёт временную папку, которая удалится после теста."""
        path = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        return path

    def write(self, **changes):
        """Пишет CSV с изменениями (None удаляет параметр)."""
        params = dict(BASE, **changes)
        params = {k: v for k, v in params.items() if v is not None}
        path = os.path.join(self.folder(), "config.csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerows(params.items())
        return path

    def test_valid(self):
        """Корректный конфиг загружается с приведёнными типами."""
        config = load_config(self.write())
        self.assertEqual(config["max_depth"], 3)
        self.assertIs(config["test_mode"], False)
        self.assertIs(config["ascii_tree"], True)

    def test_invalid_values(self):
        """Неверные значения параметров дают ValueError."""
        bad = [{"max_depth": "abc"}, {"max_depth": "-1"},
               {"test_mode": "maybe"}, {"ascii_tree": "x"},
               {"repository": "nuget.org"}, {"package_name": ""},
               {"max_depth": None}]
        for changes in bad:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    load_config(self.write(**changes))

    def test_missing_file(self):
        """Отсутствующий файл конфигурации даёт ValueError."""
        with self.assertRaises(ValueError):
            load_config(os.path.join(self.folder(), "nope.csv"))

    def test_test_mode_rules(self):
        """В тестовом режиме нужны файл и заглавные буквы."""
        good = self.write(test_mode="true", repository=REPO)
        self.assertTrue(load_config(good)["test_mode"])
        lower = self.write(test_mode="true", repository=REPO,
                           package_name="a")
        with self.assertRaises(ValueError):
            load_config(lower)
        no_file = self.write(test_mode="true", repository="nope.txt")
        with self.assertRaises(ValueError):
            load_config(no_file)


if __name__ == "__main__":
    unittest.main()