import csv
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

KEYS = ["package_name", "repository", "test_mode",
        "ascii_tree", "max_depth", "filter_substring"]

def to_bool(name, value):
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    raise ValueError(f"{name}: ожидалось true/false, получено '{value}'")


def load_config(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            params = {row[0].strip(): row[1].strip()
                      for row in csv.reader(f) if len(row) >= 2}
    except FileNotFoundError:
        raise ValueError(f"файл конфигурации не найден: {path}")

    for key in KEYS:
        if key not in params:
            raise ValueError(f"в конфиге нет параметра '{key}'")

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

def download(url):
    """Скачивает URL и возвращает байты. Сетевые ошибки -> ValueError."""
    request = urllib.request.Request(url, headers={"User-Agent": "depviz"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"ничего не найдено по адресу {url} (404)")
        raise ValueError(f"сервер вернул ошибку {e.code} для {url}")
    except urllib.error.URLError as e:
        raise ValueError(f"не удалось подключиться к {url}: {e.reason}")
    except TimeoutError:
        raise ValueError(f"превышено время ожидания ответа от {url}")


def find_package_base(index_url):
    """Из сервисного индекса достаёт адрес PackageBaseAddress."""
    try:
        index = json.loads(download(index_url))
        for resource in index["resources"]:
            if resource["@type"].startswith("PackageBaseAddress"):
                return resource["@id"].rstrip("/") + "/"
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        raise ValueError(f"{index_url} не похож на сервисный индекс NuGet v3")
    raise ValueError("в сервисном индексе нет ресурса PackageBaseAddress")


def pick_version(base, name):
    """Возвращает последнюю стабильную версию пакета."""
    url = f"{base}{name.lower()}/index.json"
    try:
        versions = json.loads(download(url))["versions"]
    except ValueError:
        raise ValueError(f"пакет '{name}' не найден в репозитории")
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError(f"неожиданный ответ сервера по адресу {url}")
    if not versions:
        raise ValueError(f"у пакета '{name}' нет версий")
    stable = [v for v in versions if "-" not in v]
    return (stable or versions)[-1]


def local(tag):
    """'{namespace}dependency' -> 'dependency'."""
    return tag.split("}")[-1]


def parse_nuspec(data):
    """Разбирает .nuspec. Возвращает {платформа: [(id, версия), ...]}."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise ValueError("не удалось разобрать .nuspec (некорректный XML)")

    result = {}
    for element in root.iter():
        if local(element.tag) != "dependencies":
            continue
        for child in element:
            kind = local(child.tag)
            if kind == "group":
                framework = child.get("targetFramework") or "любая платформа"
                items = [d for d in child if local(d.tag) == "dependency"]
            elif kind == "dependency":
                framework = "любая платформа"
                items = [child]
            else:
                continue
            for d in items:
                result.setdefault(framework, []).append(
                    (d.get("id"), d.get("version", "")))
    return result


def get_direct_dependencies(index_url, name):
    """Главная функция этапа: возвращает (версия, зависимости по платформам)."""
    base = find_package_base(index_url)
    version = pick_version(base, name)
    lower = name.lower()
    nuspec = download(f"{base}{lower}/{version}/{lower}.nuspec")
    return version, parse_nuspec(nuspec)


def print_dependencies(name, version, deps):
    print(f"\nПакет {name} версии {version}")
    if not deps or all(len(items) == 0 for items in deps.values()):
        print("Прямых зависимостей нет")
        return
    print("Прямые зависимости:")
    for framework, items in deps.items():
        if items:
            print(f"  [{framework}]")
            for dep_id, dep_version in items:
                print(f"    - {dep_id} {dep_version}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "config.csv"
    try:
        config = load_config(path)
        for key, value in config.items():
            print(f"{key} = {value}")

        if config["test_mode"]:
            print("\nТестовый режим будет реализован на этапе 3")
        else:
            version, deps = get_direct_dependencies(
                config["repository"], config["package_name"])
            print_dependencies(config["package_name"], version, deps)
    except ValueError as e:
        print("Ошибка:", e)
        sys.exit(1)