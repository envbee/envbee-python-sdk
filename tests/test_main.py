import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from envbee_sdk.main import Envbee

logger = logging.getLogger(__name__)


class Test(TestCase):
    """Test suite for the envbee SDK methods."""

    def setUp(self):
        """Set up the test environment before each test."""
        super().setUp()

    def tearDown(self):
        """Clean up the test environment after each test."""
        super().tearDown()

    @patch("envbee_sdk.main.requests.get")
    def test_get_variable_simple(self, mock_get: MagicMock):
        """Test getting a variable successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"name": "Var1", "value": "Value1"}

        eb = Envbee("1__local", b"key---1")
        self.assertEqual("Value1", eb.get_variable("Var1"))

    @patch("envbee_sdk.main.requests.get")
    def test_get_variable_cache(self, mock_get: MagicMock):
        """Test retrieving a variable from cache when the API request fails."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "name": "Var1",
            "value": "ValueFromCache",
        }

        eb = Envbee("1__local", b"key---1")
        self.assertEqual("ValueFromCache", eb.get_variable("Var1"))

        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {}
        eb = Envbee("1__local", b"key---1")
        self.assertEqual("ValueFromCache", eb.get_variable("Var1"))

    @patch("envbee_sdk.main.requests.get")
    def test_get_variables_simple(self, mock_get: MagicMock):
        """Test getting multiple variables successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "metadata": {"limit": 1, "offset": 10, "total": 100},
            "data": [
                {"name": "VAR1", "value": "VALUE1"},
                {"name": "VAR2", "value": [1, 2, 3]},
            ],
        }

        eb = Envbee("1__local", b"key---1")
        variables = eb.get_variables()
        self.assertEqual(
            "VALUE1", list(filter(lambda x: x["name"] == "VAR1", variables))[0]["value"]
        )

    @patch("envbee_sdk.main.requests.get")
    def test_get_variables_cache(self, mock_get: MagicMock):
        """Test retrieving multiple variables from cache when the API request fails."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "metadata": {"limit": 50, "offset": 0, "total": 2},
            "data": [
                {"name": "V1", "value": "VALUE_CACHE"},
                {"name": "V2", "value": [3, 4, 5]},
            ],
        }

        eb = Envbee("1__local", b"key---1")
        variables = eb.get_variables()
        self.assertEqual(
            "VALUE_CACHE",
            list(filter(lambda x: x["name"] == "V1", variables))[0]["value"],
        )

        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {}
        eb = Envbee("1__local", b"key---1")
        variables = eb.get_variables()
        self.assertEqual(
            "VALUE_CACHE",
            list(filter(lambda x: x["name"] == "V1", variables))[0]["value"],
        )
