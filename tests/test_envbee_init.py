import os
import unittest
from envbee_sdk.main import Envbee


class TestEnvbeeInit(unittest.TestCase):
    def setUp(self):
        # Backup environment variables
        self._original_environ = os.environ.copy()

    def tearDown(self):
        # Restore environment variables after each test
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_init_with_all_parameters(self):
        client = Envbee(
            api_key="key123",
            api_secret="secret123",
            base_url="https://custom.url",
            enc_key="encryption-key",
        )
        self.assertIsInstance(client, Envbee)

    def test_init_from_environment_variables(self):
        os.environ["ENVBEE_API_KEY"] = "key-env"
        os.environ["ENVBEE_API_SECRET"] = "secret-env"
        os.environ["ENVBEE_API_URL"] = "https://from.env"
        os.environ["ENVBEE_ENC_KEY"] = "enc-env"

        client = Envbee()  # No parameters
        self.assertIsInstance(client, Envbee)

    def test_missing_api_key(self):
        # Only set secret
        os.environ["ENVBEE_API_SECRET"] = "secret-env"
        with self.assertRaises(ValueError) as ctx:
            Envbee()
        self.assertIn("api_key", str(ctx.exception))

    def test_missing_api_secret(self):
        # Only set key
        os.environ["ENVBEE_API_KEY"] = "key-env"
        with self.assertRaises(ValueError) as ctx:
            Envbee()
        self.assertIn("api_secret", str(ctx.exception))

    def test_priority_parameters_over_environment(self):
        os.environ["ENVBEE_API_KEY"] = "env-key"
        os.environ["ENVBEE_API_SECRET"] = "env-secret"
        client = Envbee(api_key="param-key", api_secret="param-secret")
        self.assertIsInstance(client, Envbee)

    def test_init_without_enc_key(self):
        client = Envbee(api_key="key123", api_secret="secret123")
        self.assertIsInstance(client, Envbee)
        # Internals are private, so we rely on no exception raised
