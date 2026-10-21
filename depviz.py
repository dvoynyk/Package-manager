import csv
import os
import sys

# Параметры, которые должны быть в конфиге
KEYS = ["package_name", "repository", "test_mode",
        "ascii_tree", "max_depth", "filter_substring"]


def to_bool(name, value):
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    raise ValueError(f"{name}: ожидалось true/false, получено '{value}'")


def load_config(path):
    # 1. Читаем CSV в словарь {параметр: значение}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            params = {row[0].strip(): row[1].strip()
                      for row in csv.reader(f) if len(row) >= 2}
    except FileNotFoundError:
        raise ValueError(f"файл конфигурации не найден: {path}")

    # 2. Проверяем, что все параметры на месте
    for key in KEYS:
        if key not in params:
            raise ValueError(f"в конфиге нет параметра '{key}'")

    # 3. Проверяем значения
    if not params["package_name"]:
        raise ValueError("package_name: имя пакета не может быть пустым")

    test_mode = to_bool("test_mode", params["test_mode"])
    ascii_tree = to_bool("ascii_tree", params["ascii_tree"])

    repo = params["repository"]
    if test_mode:
        if not os.path.isfile(repo):
            raise ValueError(f"repository: файл не найден: {repo}")
    elif not repo.startswith(("http://", "https://")):
        raise ValueError(f"repository: '{repo}' не похож на URL")

    try:
        depth = int(params["max_depth"])
    except ValueError:
        raise ValueError(f"max_depth: '{params['max_depth']}' не целое число")
    if depth < 0:
        raise ValueError("max_depth: не может быть отрицательным")

    return {
        "package_name": params["package_name"],
        "repository": repo,
        "test_mode": test_mode,
        "ascii_tree": ascii_tree,
        "max_depth": depth,
        "filter_substring": params["filter_substring"],
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "config.csv"
    try:
        config = load_config(path)
    except ValueError as e:
        print("Ошибка:", e)
        sys.exit(1)

    for key, value in config.items():
        print(f"{key} = {value}")