
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as xml_tree

HTTP_NOT_FOUND = 404
HTTP_TOO_MANY = 429
HTTP_SERVER_ERROR = 500
ATTEMPTS = 3
TIMEOUT = 30
ANY_FRAMEWORK = "любая платформа"


class NotFoundError(ValueError):
    """Ресурс на сервере не найден (HTTP 404)."""


def is_retryable(code):
    return code == HTTP_TOO_MANY or code >= HTTP_SERVER_ERROR


def check_http_error(error, url):
    if error.code == HTTP_NOT_FOUND:
        raise NotFoundError(f"ничего не найдено по адресу {url} (404)")
    if not is_retryable(error.code):
        raise ValueError(f"сервер вернул ошибку {error.code} для {url}")


def request_once(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "depviz", "Connection": "close"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def download(url):
    last_error = ""
    for attempt in range(ATTEMPTS):
        try:
            return request_once(url)
        except urllib.error.HTTPError as error:
            check_http_error(error, url)
            last_error = f"сервер вернул ошибку {error.code}"
        except urllib.error.URLError as error:
            last_error = f"не удалось подключиться: {error.reason}"
        except OSError as error:
            last_error = f"соединение прервано: {error}"
        time.sleep(1 + attempt)
    raise ValueError(f"{url}: {last_error} (попыток: {ATTEMPTS})")


def find_package_base(index_url):
    try:
        resources = json.loads(download(index_url))["resources"]
        for resource in resources:
            if resource["@type"].startswith("PackageBaseAddress"):
                return resource["@id"].rstrip("/") + "/"
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        raise ValueError(f"{index_url} не похож на индекс NuGet v3")
    raise ValueError("в индексе нет ресурса PackageBaseAddress")


def pick_version(base, name):
    url = f"{base}{name.lower()}/index.json"
    try:
        data = download(url)
    except NotFoundError:
        raise ValueError(f"пакет '{name}' не найден в репозитории")
    try:
        versions = json.loads(data)["versions"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError(f"неожиданный ответ сервера: {url}")
    if not versions:
        raise ValueError(f"у пакета '{name}' нет версий")
    stable = [version for version in versions if "-" not in version]
    return (stable or versions)[-1]


def local(tag):
    return tag.split("}")[-1]


def parse_group(child):
    kind = local(child.tag)
    if kind == "group":
        framework = child.get("targetFramework") or ANY_FRAMEWORK
        items = [item for item in child if local(item.tag) == "dependency"]
        return framework, items
    if kind == "dependency":
        return ANY_FRAMEWORK, [child]
    return ANY_FRAMEWORK, []


def parse_nuspec(data):
    try:
        root = xml_tree.fromstring(data)
    except xml_tree.ParseError:
        raise ValueError("не удалось разобрать .nuspec (некорректный XML)")
    result = {}
    for element in root.iter():
        if local(element.tag) != "dependencies":
            continue
        for child in element:
            framework, items = parse_group(child)
            for item in items:
                result.setdefault(framework, []).append(
                    (item.get("id"), item.get("version", "")))
    return result


def collect_names(deps_by_framework):
    names = []
    for items in deps_by_framework.values():
        for dep_id, _ in items:
            if dep_id and dep_id not in names:
                names.append(dep_id)
    return names


def make_nuget_getter(index_url):
    base = find_package_base(index_url)

    def get_deps(name):
        version = pick_version(base, name)
        lower = name.lower()
        url = f"{base}{lower}/{version}/{lower}.nuspec"
        return collect_names(parse_nuspec(download(url)))

    return get_deps