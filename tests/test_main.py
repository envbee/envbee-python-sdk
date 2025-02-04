import logging
from dataclasses import asdict
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
    def test_get_variable_value_simple(self, mock_get: MagicMock):
        """Test getting a variable successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": "Value1"}

        eb = Envbee("1__local", b"key---1")
        self.assertEqual("Value1", eb.get("Var1"))

    @patch("envbee_sdk.main.requests.get")
    def test_get_variable_cache(self, mock_get: MagicMock):
        """Test retrieving a variable from cache when the API request fails."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": "ValueFromCache"}

        eb = Envbee("1__local", b"key---1")
        self.assertEqual("ValueFromCache", eb.get("Var1"))

        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {}
        eb = Envbee("1__local", b"key---1")
        self.assertEqual("ValueFromCache", eb.get("Var1"))

    @patch("envbee_sdk.main.requests.get")
    def test_get_variables_simple(self, mock_get: MagicMock):
        """Test getting multiple variables successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "metadata": {"limit": 1, "offset": 10, "total": 100},
            "data": [
                {"id": 1, "type": "STRING", "name": "VAR1", "description": "desc1"},
                {"id": 2, "type": "BOOLEAN", "name": "VAR2", "description": "desc2"},
            ],
        }

        eb = Envbee("1__local", b"key---1")
        variables, md = eb.get_variables()
        self.assertEqual(
            "desc1",
            list(filter(lambda x: x["name"] == "VAR1", variables))[0]["description"],
        )
        self.assertAlmostEqual({"limit": 1, "offset": 10, "total": 100}, asdict(md))
