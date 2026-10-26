"""Тесты разбора данных NuGet (без обращения к сети)."""

import json
import unittest
from unittest import mock

import nuget

NUSPEC = b"""<?xml version="1.0"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <dependencies>
      <group targetFramework="net8.0">
        <dependency id="Alpha" version="1.0.0" />
      </group>
      <group targetFramework=".NETStandard2.0">
        <dependency id="Alpha" version="1.0.0" />
        <dependency id="Beta" version="2.0.0" />
      </group>
    </dependencies>
  </metadata>
</package>"""

FLAT = b"""<package><metadata><dependencies>
  <dependency id="Gamma" version="1.0" />
</dependencies></metadata></package>"""


class NugetTest(unittest.TestCase):
    """Проверка разбора .nuspec и цепочки запросов."""

    def test_groups(self):
        """Зависимости группируются по платформам."""
        result = nuget.parse_nuspec(NUSPEC)
        self.assertEqual(set(result), {"net8.0", ".NETStandard2.0"})
        self.assertEqual(result[".NETStandard2.0"][1], ("Beta", "2.0.0"))

    def test_without_group(self):
        """Старый формат без group тоже поддерживается."""
        result = nuget.parse_nuspec(FLAT)
        self.assertEqual(result[nuget.ANY_FRAMEWORK], [("Gamma", "1.0")])

    def test_no_dependencies(self):
        """Пакет без блока dependencies даёт пустой результат."""
        self.assertEqual(nuget.parse_nuspec(b"<package/>"), {})

    def test_invalid_xml(self):
        """Битый XML даёт ValueError."""
        with self.assertRaises(ValueError):
            nuget.parse_nuspec(b"<not xml")

    def test_collect_names(self):
        """Имена всех платформ объединяются без повторов."""
        names = nuget.collect_names(nuget.parse_nuspec(NUSPEC))
        self.assertEqual(names, ["Alpha", "Beta"])

    def test_getter_offline(self):
        """Цепочка индекс -> версия -> nuspec работает без сети."""
        index = json.dumps({"resources": [{
            "@type": "PackageBaseAddress/3.0.0", "@id": "https://x/"}]})
        versions = json.dumps({"versions": ["1.0.0", "1.5.0", "2.0.0-b"]})
        responses = {
            "https://idx": index.encode(),
            "https://x/pkg/index.json": versions.encode(),
            "https://x/pkg/1.5.0/pkg.nuspec": NUSPEC,
        }
        with mock.patch("nuget.download",
                        side_effect=responses.__getitem__):
            get_deps = nuget.make_nuget_getter("https://idx")
            self.assertEqual(get_deps("Pkg"), ["Alpha", "Beta"])

    def test_package_not_found(self):
        """404 на списке версий превращается в 'пакет не найден'."""
        with mock.patch("nuget.download",
                        side_effect=nuget.NotFoundError("404")):
            with self.assertRaises(ValueError) as context:
                nuget.pick_version("https://x/", "Pkg")
        self.assertIn("не найден", str(context.exception))


if __name__ == "__main__":
    unittest.main()