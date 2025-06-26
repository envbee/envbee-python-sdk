# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------

import base64
import logging
import os
from dataclasses import asdict
from unittest import TestCase
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from envbee_sdk.exceptions.envbee_exceptions import DecryptionError
from envbee_sdk.main import ENC_PREFIX, Envbee

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
            list(filter(lambda x: x["name"] == "VAR1", variables))[0]["description"],
        )
        self.assertAlmostEqual({"limit": 1, "offset": 10, "total": 100}, asdict(md))
