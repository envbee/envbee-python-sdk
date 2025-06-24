# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------

"""
envbee API Client.

This class provides methods to interact with the envbee API, allowing users to retrieve
and manage environment variables through secure authenticated requests.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version

import platformdirs
import requests
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from diskcache import Cache

from .constants import ENC_PREFIX
from .exceptions.envbee_exceptions import (
    DecryptionError,
    RequestError,
    RequestTimeoutError,
)
from .metadata import Metadata
from .utils import add_querystring

logger = logging.getLogger(__name__)


try:
    __version__ = version("envbee_sdk")  # Use package name as `pyproject.toml`
except PackageNotFoundError:
    __version__ = "unknown"


class Envbee:
    __ENVAR_API_KEY = "ENVBEE_API_KEY"
    __ENVAR_API_SECRET = "ENVBEE_API_SECRET"
    __ENVAR_API_URL = "ENVBEE_API_URL"
    __ENVAR_ENC_KEY = "ENVBEE_ENC_KEY"
    __BASE_URL: str = "https://api.envbee.dev"

    __base_url: str
    __api_key: str | None
    __api_secret: bytes | None
    __aesgcm: AESGCM | None

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: bytes | bytearray | str | None = None,
        base_url: str | None = None,
        enc_key: bytes | bytearray | str | None = None,
    ) -> None:
        """Initialize the API client with necessary credentials.

        Args:
            api_key (str): The unique identifier for the API.
            api_secret (bytes | bytearray | str): The secret key used for authenticating API requests.
            base_url (str, optional): The base URL for the API. Defaults to https://api.envbee.dev URL if not provided.
            enc_key (bytes | bytearray | str | None, optional): The client-side encryption key used to decrypt variable values.
                Must be 16, 24, or 32 bytes long to match AES-GCM key requirements.
                If not provided, encrypted variables cannot be decrypted.
        """
        logger.debug("Initializing Envbee client.")

        ENVBEE_API_KEY = os.getenv(self.__ENVAR_API_KEY)
        ENVBEE_API_SECRET = os.getenv(self.__ENVAR_API_SECRET)
        ENVBEE_API_URL: str = os.getenv(self.__ENVAR_API_URL, self.__BASE_URL)
        ENVBEE_ENC_KEY = os.getenv(self.__ENVAR_ENC_KEY)

        self.__base_url = base_url or ENVBEE_API_URL
        self.__api_key = api_key or ENVBEE_API_KEY
        if self.__api_key is None:
            raise ValueError(
                "An api_key must be provided as a parameter or by setting ENVBEE_API_KEY environment variable"
            )

        if api_secret is None:
            api_secret = ENVBEE_API_SECRET

        if isinstance(api_secret, str):
            self.__api_secret = api_secret.encode()
        else:
            self.__api_secret = api_secret

        if self.__api_secret is None:
            raise ValueError(
                "An api_secret must be provided as a parameter or by setting ENVBEE_API_SECRET environment variable"
            )

        if enc_key is None:
            enc_key = ENVBEE_ENC_KEY

        if enc_key:
            if isinstance(enc_key, str):
                enc_key = sha256(enc_key.encode()).digest()

            if len(enc_key) not in {16, 24, 32}:  # AES key sizes in bytes
                raise ValueError("Encryption key must be 16, 24, or 32 bytes long")

            self.__aesgcm = AESGCM(enc_key)
        else:
            self.__aesgcm = None
            logger.debug("No encryption key provided")

        logger.info("Envbee client initialized with base URL: %s", self.__base_url)

    def _generate_hmac_header(self, url_path: str) -> str:
        """Generate an HMAC authentication header for the specified URL path.

        This method creates an HMAC header used for API authentication, including the current timestamp
        and a hash of the request content.

        Args:
            url_path (str): The path of the API endpoint to which the request is being made.

        Returns:
            str: The formatted HMAC authorization header.
        """
        logger.debug("Generating HMAC header for URL path: %s", url_path)
        try:
            hmac_obj = hmac.new(self.__api_secret, digestmod=hashlib.sha256)
            current_time = str(int(time.time() * 1000))
            hmac_obj.update(current_time.encode("utf-8"))
            hmac_obj.update(b"GET")
            hmac_obj.update(url_path.encode("utf-8"))
            content = json.dumps({}).encode("utf-8")
            content_hash = hashlib.md5()
            content_hash.update(content)
            hmac_obj.update(content_hash.hexdigest().encode("utf-8"))
            auth_header = "HMAC %s:%s" % (current_time, hmac_obj.hexdigest())
            logger.debug("HMAC header generated successfully.")
            return auth_header
        except Exception as e:
            logger.error("Error generating HMAC header: %s", e, exc_info=True)
            raise

    def __maybe_decrypt(self, value: str) -> str:
        """Attempt to decrypt the variable if it's encrypted with the supported format.

        Args:
            value (str): The encrypted or plain value.

        Returns:
            str: The decrypted value if encrypted, or the original value.
        """
        if isinstance(value, str) and value.startswith(ENC_PREFIX):
            if self.__aesgcm is None:
                raise DecryptionError(
                    "Encrypted variable received, but no encryption key was configured."
                )

            try:
                raw = base64.b64decode(value[len(ENC_PREFIX) :])
                nonce = raw[:12]  # AES-GCM uses a 12-byte nonce
                ciphertext_and_tag = raw[12:]
                decrypted = self.__aesgcm.decrypt(
                    nonce, ciphertext_and_tag, associated_data=None
                )
                return decrypted.decode()
            except InvalidTag as e:
                logger.warning("Decryption failed due to invalid key or tampered data.")
                raise DecryptionError(
                    "Decryption failed. Invalid key or corrupted data.", cause=e
                )
            except Exception as e:
                logger.error("Failed to decrypt variable: %s", str(e))
                raise
        return value

    def _send_request(self, url: str, hmac_header: str, timeout: int = 2):
        """Send a GET request to the specified URL with the given HMAC header.

        This method performs an authenticated API request and handles response status codes.
        If the request is successful, it returns the JSON response; otherwise, it raises an error.

        Args:
            url (str): The URL to which the GET request will be sent.
            hmac_header (str): The HMAC authentication header for the request.
            timeout (int, optional): The maximum time to wait for the request to complete (in seconds). Defaults to 2.

        Returns:
            dict: The JSON response from the API if the request is successful.

        Raises:
            RequestError: If the response status code indicates a failed request.
            RequestTimeoutError: If the request times out.
        """
        logger.debug("Sending request to URL: %s", url)
        try:
            headers = {
                "Authorization": hmac_header,
                "x-api-key": self.__api_key,
                "x-envbee-client": f"python-sdk/{__version__}",
            }
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
            )
            logger.debug("Received response with status code: %s", response.status_code)
            if response.status_code == 200:
                logger.debug("Request successful. Returning JSON response.")
                return response.json()
            else:
                logger.error(
                    "Request to failed with status code: %s. Response text: %s",
                    response.status_code,
                    response.text,
                )
                raise RequestError(
                    response.status_code, f"Failed request: {response.text}"
                )
        except requests.exceptions.Timeout:
            logger.error("Request to %s timed out after %d seconds", url, timeout)
            raise RequestTimeoutError(
                f"Request to {url} timed out after {timeout} seconds"
            )
        except Exception as e:
            logger.critical(
                "Unexpected error during request to %s: %s", url, e, exc_info=True
            )
            raise e

    def _cache_variable(self, variable_name: str, variable_value):
        """Cache a variable locally for future retrieval.

        Args:
            variable_name (str): The name of the variable to cache.
            variable_content (str): The content of the variable to cache.
        """
        logger.debug("Caching variable: %s", variable_name)
        try:
            app_cache_dir = platformdirs.user_cache_dir(
                appname=self.__api_key, appauthor="envbee"
            )
            with Cache(app_cache_dir) as reference:
                reference.set(variable_name, variable_value)
            logger.debug("Variable %s cached successfully.", variable_name)
        except Exception as e:
            logger.error(
                "Error caching variable %s: %s", variable_name, e, exc_info=True
            )

    def _get_variable_value_from_cache(self, variable_name: str) -> any:
        """Retrieve a variable's content from the local cache.

        Args:
            variable_name (str): The name of the variable to retrieve.

        Returns:
            str: The cached content of the variable, or None if not found.
        """
        logger.debug("Retrieving variable from cache: %s", variable_name)
        try:
            app_cache_dir = platformdirs.user_cache_dir(
                appname=self.__api_key, appauthor="envbee"
            )
            with Cache(app_cache_dir) as reference:
                value = reference.get(variable_name)
            if value:
                logger.debug("Variable %s retrieved from cache.", variable_name)
            else:
                logger.warning("Variable %s not found in cache.", variable_name)
            return value
        except Exception as e:
            logger.error(
                "Error retrieving variable %s from cache: %s",
                variable_name,
                e,
                exc_info=True,
            )

    def get(self, variable_name: str) -> any:
        """Retrieve a variable's value by its name.

        This method attempts to fetch the variable from the API, and if it fails, it retrieves
        the value from the local cache. If the value is encrypted (e.g., starts with __ENC_PREFIX),
        it will be decrypted using the provided encryption key.

        Args:
            variable_name (str): The name of the variable to retrieve.

        Returns:
            The decrypted or plain value of the variable.
        """
        logger.debug("Fetching variable: %s", variable_name)
        url_path = f"/v1/variables-values-by-name/{variable_name}/content"
        hmac_header = self._generate_hmac_header(url_path)
        final_url = f"{self.__base_url}{url_path}"
        try:
            response = self._send_request(final_url, hmac_header)
            value = response.get("value")
            logger.debug("Variable %s fetched successfully.", variable_name)

            # Cache encrypted or plain as-is
            self._cache_variable(variable_name, value)

            # Decrypt only when returning
            return self.__maybe_decrypt(value)
        except DecryptionError:
            # Don't fallback to cache; re-raise the error
            raise
        except Exception:
            logger.warning(
                "Failed to fetch variable %s from API. Falling back to cache.",
                variable_name,
            )
            cached = self._get_variable_value_from_cache(variable_name)
            return self.__maybe_decrypt(cached)

    def get_variables(
        self, offset: int = None, limit: int = None
    ) -> tuple[list[dict], Metadata]:
        """Retrieve a list of variables with optional pagination.

        This method fetches variables from the API.

        Args:
            offset (int, optional): The starting point for fetching variables.
            limit (int, optional): The maximum number of variables to retrieve.

        Returns:
            list[dict]: A list of dictionaries containing variables definition.
        """
        logger.debug("Fetching variables with offset=%s, limit=%s", offset, limit)
        url_path = "/v1/variables"
        params = {}
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit

        url_path = add_querystring(url_path, params)
        hmac_header = self._generate_hmac_header(url_path)
        final_url = f"{self.__base_url}{url_path}"
        try:
            result_json = self._send_request(final_url, hmac_header)
            metadata = Metadata(**result_json.get("metadata", {}))
            data = result_json.get("data", [])
            logger.debug("Fetched %d variables.", len(data))
            return data, metadata
        except Exception as e:
            logger.warning("Failed to fetch variables from API: %s", e, exc_info=True)
            raise
