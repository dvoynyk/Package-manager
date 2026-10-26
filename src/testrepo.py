"""Тестовый репозиторий: граф пакетов из текстового файла 'A: B C'."""

from config import is_test_name

SEPARATOR_COUNT = 1
COMMENT_MARK = "#"


def parse_line(line, where):
    """Разбирает строку 'A: B C' в пару (имя, список зависимостей)."""
    if line.count(":") != SEPARATOR_COUNT:
        raise ValueError(f"{where}: ожидался формат 'A: B C'")
    left, right = line.split(":")
    name, deps = left.strip(), right.split()
    for item in [name] + deps:
        if not is_test_name(item):
            raise ValueError(
                f"{where}: имя '{item}' должно состоять "
                "из заглавных латинских букв")
    return name, deps


def read_lines(path):
    """Читает файл целиком и возвращает список строк."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.readlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"не удалось прочитать {path}: {error}")


def read_test_repo(path):
    """Читает файл и возвращает словарь {пакет: [зависимости]}."""
    graph = {}
    for number, line in enumerate(read_lines(path), start=1):
        line = line.strip()
        if not line or line.startswith(COMMENT_MARK):
            continue
        where = f"{path}, строка {number}"
        name, deps = parse_line(line, where)
        if name in graph:
            raise ValueError(f"{where}: пакет '{name}' описан повторно")
        graph[name] = deps
    return graph


def make_test_getter(path):
    """Возвращает (get_deps, репозиторий) для тестового режима."""
    repo = read_test_repo(path)

    def get_deps(name):
        """Пакет без строки в файле считается пакетом без зависимостей."""
        return repo.get(name, [])

    return get_deps, repo