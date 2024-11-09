import os
import pytest
import re
import unittest
from main import (
    DOCKERFILE,
    GO_MOD_FILE,
    get_latest_go_version,
    main,
    regex_replace_go_version_in_go_mod_file,
)
import unittest
from unittest.mock import mock_open, patch, MagicMock
import requests


GO_VERSIONS_URL = "https://mocked-url.com"


def get_golang_version_from_go_mod_file() -> str:
    try:
        with open(GO_MOD_FILE, "r") as file:
            file_content = file.read()
            print(f"Content of the file:\n{file_content}")
            pattern = r"\d+\.\d+\.?\d+?"
            matches = re.findall(pattern, file_content)
            print("Extracted values:", matches[0])
            return matches[0]
    except FileNotFoundError:
        print(f"File not found: {GO_MOD_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_golang_version_from_dockerfile() -> str:
    try:
        with open(DOCKERFILE, "r") as file:
            file_content = file.read()
            print(f"Content of the file:\n{file_content}")
            pattern = r"FROM\sgolang:(\d+\.\d+\.?\d+?)"
            matches = re.findall(pattern, file_content)
            print("Extracted values:", matches[0])
            return matches[0]
    except FileNotFoundError:
        print(f"File not found: {DOCKERFILE}")
    except Exception as e:
        print(f"An error occurred: {e}")


def setup_helper_create_go_mod_with_a_golang_version(version: str):
    with open(GO_MOD_FILE, "w") as file:
        file.write("module github.com/030/gomod-go-version-updater-action\n\n")
        file.write("go " + version + "\n\n")
        file.write("require (\n")
        file.write("github.com/go-openapi/errors v0.21.1\n")
        file.write("github.com/aws/aws-sdk-go v1.50.30\n")
        file.write(")")


def setup_helper_create_dockerfile_with_a_golang_version(version: str):
    with open(DOCKERFILE, "w") as file:
        file.write("FROM anchore/grype:v0.84.0 AS grype\n")
        file.write("\n")
        file.write("FROM golang:" + version + "\n")
        file.write("ENV HOME=/home/${USERNAME} (\n")
        file.write("COPY . /go/${USERNAME}/\n")


def cleanup_helper():
    try:
        if os.path.exists(GO_MOD_FILE):
            os.remove(GO_MOD_FILE)
            print(f"The file '{GO_MOD_FILE}' has been successfully removed.")
        if os.path.exists(DOCKERFILE):
            os.remove(DOCKERFILE)
            print(f"The file '{DOCKERFILE}' has been successfully removed.")
    except Exception as e:
        pytest.fail(f"An error occurred while trying to remove the file: {e}")


class TestUpdateGolangVersionInGoModFile(unittest.TestCase):
    latest_major, latest_minor, latest_patch = get_latest_go_version()

    def tearDown(self):
        cleanup_helper()

    def test_update_golang_version_consisting_of_major_minor_and_patch(self):
        setup_helper_create_go_mod_with_a_golang_version("1.2.3")
        main()
        self.assertEqual(
            get_golang_version_from_go_mod_file(),
            TestUpdateGolangVersionInGoModFile.latest_major
            + "."
            + TestUpdateGolangVersionInGoModFile.latest_minor
            + "."
            + TestUpdateGolangVersionInGoModFile.latest_patch,
        )

    def test_update_golang_version_consisting_of_major_and_minor(self):
        setup_helper_create_go_mod_with_a_golang_version("4.2")
        main()
        self.assertEqual(
            get_golang_version_from_go_mod_file(),
            TestUpdateGolangVersionInGoModFile.latest_major
            + "."
            + TestUpdateGolangVersionInGoModFile.latest_minor,
        )

    def test_update_golang_version_consisting_of_major(self):
        setup_helper_create_go_mod_with_a_golang_version("42")
        with pytest.raises(
            ValueError,
            match="An error occurred: No Go version defined in file: go.mod",
        ):
            main()


class TestGetLatestGoVersion(unittest.TestCase):
    @patch("requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"version": "go1.18.3"}]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        major, minor, patch = get_latest_go_version()

        self.assertEqual(major, "1")
        self.assertEqual(minor, "18")
        self.assertEqual(patch, "3")

    @patch("requests.get")
    def test_non_matching_version_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"version": "invalid_version"}]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        major, minor, patch = get_latest_go_version()

        self.assertEqual(major, "")
        self.assertEqual(minor, "")
        self.assertEqual(patch, "")

    @patch("requests.get")
    def test_http_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        with self.assertRaises(SystemExit):  # Expecting the function to exit
            get_latest_go_version()


class TestRegexReplaceGoVersionInGoModFile(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="module example.com\n\ngo 1.18\n",
    )
    @patch("logging.info")
    def test_successful_replacement(self, mock_logging_info, mock_file):
        current_version = "1.18"
        replacement = "1.19"

        regex_replace_go_version_in_go_mod_file(current_version, replacement)

        mock_file().write.assert_called_once_with(
            "module example.com\n\ngo 1.19\n"
        )
        mock_logging_info.assert_called_once_with(
            f"Updated Go version in go.mod from {current_version} to {replacement}"
        )

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("logging.info")
    def test_file_not_found(self, mock_logging_info, mock_file):
        current_version = "1.18"
        replacement = "1.19"

        regex_replace_go_version_in_go_mod_file(current_version, replacement)

        mock_logging_info.assert_called_once_with(
            f"File not found: {GO_MOD_FILE}"
        )

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="module example.com\n\ngo 1.18\n",
    )
    @patch("logging.info")
    def test_general_exception(self, mock_logging_info, mock_file):
        mock_file.side_effect = Exception("Some error")

        current_version = "1.18"
        replacement = "1.19"

        regex_replace_go_version_in_go_mod_file(current_version, replacement)

        mock_logging_info.assert_called_once_with(
            "An error occurred: Some error"
        )


class TestMainFunction(unittest.TestCase):
    @patch("main.regex_replace_go_version_in_go_mod_file")
    @patch(
        "main.determine_whether_go_version_in_go_mod_file_contains_patch_version"
    )
    @patch("main.get_latest_go_version")
    @patch("main.configure_logging")
    def test_main_with_patch_version(
        self,
        mock_configure_logging,
        mock_get_latest_go_version,
        mock_determine_version,
        mock_regex_replace,
    ):
        mock_get_latest_go_version.return_value = ("1", "19", "3")
        mock_determine_version.return_value = ("1.18.0", True)

        main()

        mock_configure_logging.assert_called_once()
        mock_get_latest_go_version.assert_called_once()
        mock_determine_version.assert_called_once()
        mock_regex_replace.assert_called_once_with("1.18.0", "1.19.3")

    @patch("main.regex_replace_go_version_in_go_mod_file")
    @patch(
        "main.determine_whether_go_version_in_go_mod_file_contains_patch_version"
    )
    @patch("main.get_latest_go_version")
    @patch("main.configure_logging")
    def test_main_without_patch_version(
        self,
        mock_configure_logging,
        mock_get_latest_go_version,
        mock_determine_version,
        mock_regex_replace,
    ):
        mock_get_latest_go_version.return_value = ("1", "19", "3")
        mock_determine_version.return_value = ("1.18", False)

        main()

        mock_configure_logging.assert_called_once()
        mock_get_latest_go_version.assert_called_once()
        mock_determine_version.assert_called_once()
        mock_regex_replace.assert_called_once_with("1.18", "1.19")


if __name__ == "__main__":
    unittest.main()


class TestUpdateGolangVersionInDockerfile(unittest.TestCase):
    latest_major, latest_minor, latest_patch = get_latest_go_version()

    def tearDown(self):
        cleanup_helper()

    def test_update_golang_version_consisting_of_major_minor_and_patch_in_dockerfile(
        self,
    ):
        setup_helper_create_dockerfile_with_a_golang_version("4.2.0")
        main()
        self.assertEqual(
            get_golang_version_from_dockerfile(),
            TestUpdateGolangVersionInDockerfile.latest_major
            + "."
            + TestUpdateGolangVersionInDockerfile.latest_minor
            + "."
            + TestUpdateGolangVersionInDockerfile.latest_patch,
        )

    def test_update_golang_version_consisting_of_major_and_minor_in_dockerfile(
        self,
    ):
        setup_helper_create_dockerfile_with_a_golang_version("8.4")
        main()
        self.assertEqual(
            get_golang_version_from_dockerfile(),
            TestUpdateGolangVersionInDockerfile.latest_major
            + "."
            + TestUpdateGolangVersionInDockerfile.latest_minor,
        )

    def test_update_golang_version_consisting_of_major_minor_patch_and_alpine_as_builder_in_dockerfile(
        self,
    ):
        setup_helper_create_dockerfile_with_a_golang_version(
            "1.2.3-alpine AS builder"
        )
        main()
        self.assertEqual(
            get_golang_version_from_dockerfile(),
            TestUpdateGolangVersionInDockerfile.latest_major
            + "."
            + TestUpdateGolangVersionInDockerfile.latest_minor
            + "."
            + TestUpdateGolangVersionInDockerfile.latest_patch,
        )
