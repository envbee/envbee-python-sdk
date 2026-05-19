# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------

import base64
import logging
import os
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from envbee_sdk.exceptions.envbee_exceptions import DecryptionError
from envbee_sdk.main import ENC_PREFIX, Envbee
from envbee_sdk.model import Metadata, VariableType

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
    def test_get_variable_value_number(self, mock_get: MagicMock):
        """Test getting a variable, which is a number, successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": 1234}

        eb = Envbee("1__local", b"key---1")
        self.assertEqual(1234, eb.get("Var1234"))

    @patch("envbee_sdk.main.requests.get")
    def test_get_variable_value_encrypted_from_CLI(self, mock_get: MagicMock):
        """Test decrypting a variable encrypted by the CLI."""
        key = "0123456789abcdef0123456789abcdef"
        encrypted_value = "envbee:enc:v1:d0ktKfDJB4CIPbRmXfOmVlCU8ZCx4fl/2eZtkjgbqJy3g569ZGDEqnVOP94pDfw2Jg=="
        plaintext = "super-secret-password"

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": encrypted_value}

        eb = Envbee("1__local", b"key---1", enc_key=key)
        result = eb.get("EncryptedVar")

        self.assertEqual(result, plaintext)

    @patch("envbee_sdk.main.requests.get")
    def test_get_variable_value_encrypted(self, mock_get: MagicMock):
        """Test getting an encrypted variable and decrypting it correctly."""
        key = b"0123456789abcdef0123456789abcdef"  # 32 bytes key
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 12 bytes nonce for AES-GCM
        plaintext = b"SuperSecretValue"

        # Encrypt: ciphertext includes the tag at the end
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)

        # Format: nonce + ciphertext+tag
        encoded = base64.b64encode(nonce + ciphertext).decode()
        encrypted_value = ENC_PREFIX + encoded

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": encrypted_value}

        eb = Envbee("1__local", b"key---1", enc_key=key)
        result = eb.get("EncryptedVar")

        self.assertEqual(result, plaintext.decode())

    @patch("envbee_sdk.main.requests.get")
    def test_encrypted_value_without_key_raises(self, mock_get: MagicMock):
        """Test that an encrypted value raises an error if no encryption key is provided."""
        key = b"0123456789abcdef0123456789abcdef"
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        plaintext = b"NoKeyErrorExpected"
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)

        encoded = base64.b64encode(nonce + ciphertext).decode()
        encrypted_value = ENC_PREFIX + encoded

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": encrypted_value}

        eb = Envbee("1__local", b"key---1")  # No enc_key

        with self.assertRaises(DecryptionError) as ctx:
            eb.get("SensitiveVar")

        self.assertIn(
            "Encrypted variable received, but no encryption key was configured",
            str(ctx.exception),
        )

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
            list(filter(lambda x: x.name == "VAR1", variables))[0].description,
        )
        self.assertEqual(Metadata(limit=1, offset=10, total=100), md)

    @patch("envbee_sdk.main.requests.get")
    def test_get_variables_values(self, mock_get: MagicMock):
        """Test getting multiple variables with their values successfully from the API."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "metadata": {"limit": 2, "offset": 0, "total": 2},
            "data": [
                {
                    "id": 1,
                    "variable_id": 1,
                    "content": { "value": "Value1" }
                },
                {
                    "id": 2,
                    "variable_id": 2,
                    "content": { "value": True }
                },
            ],
        }

        eb = Envbee("1__local", b"key---1")
        variables, md = eb.get_variables_values()
        self.assertEqual(
            "Value1",
            list(filter(lambda x: x.variable_id == 1, variables))[0].content.get("value"),
        )
        self.assertEqual(Metadata(limit=2, offset=0, total=2), md)

    def test_get_variables(self):
        """Test getting variables with values and filling environment variables."""
        with patch("envbee_sdk.main.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "metadata": {"limit": 2, "offset": 0, "total": 2},
                "data": [
                    {
                        "id": 1,
                        "name": "VAR1",
                        "type": VariableType.STRING.value,
                        "description": "desc1",
                    },
                    {
                        "id": 2,
                        "name": "VAR2",
                        "type": VariableType.BOOLEAN.value,
                        "description": "desc2"
                    },
                ],
            }

            eb = Envbee("1__local", b"key---1")
            variables, md = eb.get_variables()

            self.assertEqual(
                "desc1",
                list(filter(lambda x: x.name == "VAR1", variables))[0].description
            )
            self.assertEqual(Metadata(limit=2, offset=0, total=2), md)

    def test_fill_env_vars(self):
        """Test filling environment variables from the API."""

        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = {
            "metadata": {"limit": 2, "offset": 0, "total": 2},
            "data": [
                {
                    "id": 1,
                    "name": "VAR1",
                    "type": VariableType.STRING.value,
                    "description": "desc1",
                },
                {
                    "id": 2,
                    "name": "VAR2",
                    "type": VariableType.BOOLEAN.value,
                    "description": "desc2",
                },
            ],
        }

        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = {
            "metadata": {"limit": 2, "offset": 0, "total": 2},
            "data": [
                {
                    "id": 1,
                    "variable_id": 1,
                    "content": { "value": "Value1" }
                },
                {
                    "id": 2,
                    "variable_id": 2,
                    "content": { "value": True }
                },
            ],
        }

        with patch("envbee_sdk.main.requests.get") as mock_get:
            mock_get.side_effect = [response1, response2]

            eb = Envbee("1__local", b"key---1")
            eb.fill_env_vars()

            self.assertEqual(os.environ.get("VAR1"), "Value1")
            self.assertEqual(os.environ.get("VAR2"), "True")

    def test_fill_env_vars_cache_fallback(self):
        """Test filling environment variables from cache when API calls fail."""
        with tempfile.TemporaryDirectory() as tmp_cache_dir, patch(
            "envbee_sdk.main.platformdirs.user_cache_dir", return_value=tmp_cache_dir
        ):
            eb = Envbee("1__local_fill_cache", b"key---1")

            # Prime cache with values using successful get() calls.
            with patch("envbee_sdk.main.requests.get") as mock_get:
                response_var1 = Mock()
                response_var1.status_code = 200
                response_var1.json.return_value = {"value": "ValueFromCache1"}

                response_var2 = Mock()
                response_var2.status_code = 200
                response_var2.json.return_value = {"value": True}

                mock_get.side_effect = [response_var1, response_var2]
                self.assertEqual("ValueFromCache1", eb.get("VAR1"))
                self.assertEqual(True, eb.get("VAR2"))

            # Ensure values are set from cache when the API fails.
            os.environ.pop("VAR1", None)
            os.environ.pop("VAR2", None)

            with patch("envbee_sdk.main.requests.get") as mock_get:
                failed_response = Mock()
                failed_response.status_code = 500
                failed_response.text = "Server Error"
                mock_get.return_value = failed_response

                eb.fill_env_vars()

            self.assertEqual(os.environ.get("VAR1"), "ValueFromCache1")
            self.assertEqual(os.environ.get("VAR2"), "True")


    def test_custom_cache_path(self):
        """Test that a custom cache_path can be used."""
        with tempfile.TemporaryDirectory() as tmp_cache_dir, patch("envbee_sdk.main.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"value": "ValueCustomPath"}

            eb = Envbee("1__local_custom_cache", b"key---1", cache_path=tmp_cache_dir)
            self.assertEqual("ValueCustomPath", eb.get("VAR_CUSTOM_PATH"))
            self.assertTrue(os.path.isdir(tmp_cache_dir))

    @patch("envbee_sdk.main.requests.get")
    @patch("envbee_sdk.main.os.makedirs", side_effect=PermissionError("No permission"))
    def test_memory_cache_fallback_when_disk_cache_unavailable(
        self, _mock_makedirs: MagicMock, mock_get: MagicMock
    ):
        """Test that cache falls back to in-memory when disk cache is unavailable."""
        response_ok = Mock()
        response_ok.status_code = 200
        response_ok.json.return_value = {"value": "ValueFromMemoryCache"}

        response_fail = Mock()
        response_fail.status_code = 500
        response_fail.text = "Server Error"

        mock_get.side_effect = [response_ok, response_fail]

        eb = Envbee("1__local_memory_cache", b"key---1")
        self.assertEqual("ValueFromMemoryCache", eb.get("VAR_MEMORY_CACHE"))
        self.assertEqual("ValueFromMemoryCache", eb.get("VAR_MEMORY_CACHE"))


    @patch("envbee_sdk.main.requests.get")
    def test_timeout_seconds_override(self, mock_get: MagicMock):
        """Test that timeout_seconds is passed to requests."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": "Value1"}

        eb = Envbee("1__local", b"key---1", timeout_seconds=7)
        self.assertEqual("Value1", eb.get("Var1"))
        self.assertEqual(mock_get.call_args.kwargs.get("timeout"), 7)

    @patch("envbee_sdk.main.requests.get")
    def test_timeout_seconds_default_is_4(self, mock_get: MagicMock):
        """Test that default request timeout is 4 seconds."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"value": "Value1"}

        eb = Envbee("1__local", b"key---1")
        self.assertEqual("Value1", eb.get("Var1"))
        self.assertEqual(mock_get.call_args.kwargs.get("timeout"), 4.0)
