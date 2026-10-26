"""Чтение и проверка конфигурации из CSV-файла."""

import csv
import os

KEYS = (
    "package_name", "repository", "test_mode",
    "ascii_tree", "max_depth", "filter_substring",
)
TRUE_VALUES = ("true", "yes", "1")
FALSE_VALUES = ("false", "no", "0")
URL_PREFIXES = ("http://", "https://")
MIN_DEPTH = 0
COLUMNS = 2


def to_bool(name, value):
    """Преобразует строку в bool или сообщает об ошибке."""
    text = value.lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    raise ValueError(f"{name}: ожидалось true/false, получено '{value}'")


def is_test_name(name):
    """Проверяет, что имя состоит из заглавных латинских букв."""
    return name.isascii() and name.isalpha() and name.isupper()


def read_params(path):
    """Читает CSV вида 'параметр,значение' в словарь."""
    try:
        with open(path, newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
    except FileNotFoundError:
        raise ValueError(f"файл конфигурации не найден: {path}")
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise ValueError(f"не удалось прочитать {path}: {error}")
    return {row[0].strip(): row[1].strip()
            for row in rows if len(row) >= COLUMNS}


def check_keys(params):
    """Проверяет, что в конфиге есть все обязательные параметры."""
    for key in KEYS:
        if key not in params:
            raise ValueError(f"в конфиге нет параметра '{key}'")


def parse_depth(raw):
    """Преобразует max_depth в неотрицательное целое число."""
    try:
        depth = int(raw)
    except ValueError:
        raise ValueError(f"max_depth: '{raw}' не целое число")
    if depth < MIN_DEPTH:
        raise ValueError("max_depth: не может быть отрицательным")
    return depth


def check_repository(repo, name, test_mode):
    """Проверяет repository и имя пакета с учётом режима работы."""
    if not test_mode:
        if not repo.startswith(URL_PREFIXES):
            raise ValueError(f"repository: '{repo}' не похож на URL")
        return
    if not os.path.isfile(repo):
        raise ValueError(f"repository: файл не найден: {repo}")
    if not is_test_name(name):
        raise ValueError(
            "package_name: в тестовом режиме нужны заглавные латинские "
            f"буквы, получено '{name}'")


def load_config(path):
    """Загружает конфигурацию и возвращает проверенный словарь."""
    params = read_params(path)
    check_keys(params)
    name = params["package_name"]
    if not name:
        raise ValueError("package_name: имя пакета не может быть пустым")
    test_mode = to_bool("test_mode", params["test_mode"])
    check_repository(params["repository"], name, test_mode)
    return {
        "package_name": name,
        "repository": params["repository"],
        "test_mode": test_mode,
        "ascii_tree": to_bool("ascii_tree", params["ascii_tree"]),
        "max_depth": parse_depth(params["max_depth"]),
        "filter_substring": params["filter_substring"],
    }