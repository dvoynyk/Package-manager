

import sys

from config import load_config
from graph import build_graph
from nuget import make_nuget_getter
from output import render_list, render_tree
from testrepo import make_test_getter

DEFAULT_CONFIG = "config.csv"


def choose_getter(config):
    if not config["test_mode"]:
        return make_nuget_getter(config["repository"])
    get_deps, repo = make_test_getter(config["repository"])
    root = config["package_name"]
    if root not in repo:
        raise ValueError(
            f"пакет '{root}' не описан в тестовом репозитории")
    return get_deps


def run(config_path):
    config = load_config(config_path)
    root = config["package_name"]
    substring = config["filter_substring"]
    if substring and substring in root:
        raise ValueError(f"пакет '{root}' исключён фильтром '{substring}'")
    get_deps = choose_getter(config)
    graph = build_graph(root, get_deps, config["max_depth"], substring)
    if config["ascii_tree"]:
        return render_tree(graph, root, config["max_depth"])
    return render_list(graph)


def main(argv):
    path = (argv[1:] or [DEFAULT_CONFIG])[0]
    try:
        lines = run(path)
    except ValueError as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))