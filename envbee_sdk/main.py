# ------------------------------------
# Copyright (c) envbee
# Licensed under the MIT License.
# ------------------------------------

"""
envbee API Client.

This class provides methods to interact with the envbee API, allowing users to retrieve
and manage environment variables through secure authenticated requests.
"""

import hashlib
import hmac
import json
import logging
import time

import platformdirs
import requests
from diskcache import Cache

from .exceptions.envbee_exceptions import RequestError, RequestTimeoutError
from .metadata import Metadata
from .utils import add_querystring

logger = logging.getLogger(__name__)


class Envbee:
    __BASE_URL: str = "https://api.envbee.dev"

    __base_url: str
    __api_key: str
    __api_secret: bytes

    def __init__(
        self, api_key: str, api_secret: bytes | bytearray | str, base_url: str = None
    ) -> None:
        """Initialize the API client with necessary credentials.

        Args:
            api_key (str): The unique identifier for the API.
            api_secret (bytes | bytearray | str): The secret key used for authenticating API requests.
            base_url (str, optional): The base URL for the API. Defaults to https://api.envbee.dev URL if not provided.
        """
        logger.debug("Initializing Envbee client.")
        self.__base_url = base_url or self.__BASE_URL
        self.__api_key = api_key
        if isinstance(api_secret, str):
            self.__api_secret = api_secret.encode()
        else:
            self.__api_secret = api_secret
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
            response = requests.get(
                url,
                headers={"Authorization": hmac_header, "x-api-key": self.__api_key},
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
        the value from the local cache.

        Args:
            variable_name (str): The name of the variable to retrieve.

        Returns:
            The value of the variable.
        """
        logger.debug("Fetching variable: %s", variable_name)
        url_path = f"/v1/variables-values-by-name/{variable_name}/content"
        hmac_header = self._generate_hmac_header(url_path)
        final_url = f"{self.__base_url}{url_path}"
        try:
            response = self._send_request(final_url, hmac_header)
            value = response.get("value")
            self._cache_variable(variable_name, value)
            logger.debug("Variable %s fetched successfully.", variable_name)
            return value
        except Exception:
            logger.warning(
                "Failed to fetch variable %s from API. Falling back to cache.",
                variable_name,
            )
            return self._get_variable_value_from_cache(variable_name)

    def get_variables(
        self, offset: int = None, limit: int = None
    ) -> tuple[list[dict], Metadata]:
        """Retrieve a list of variables with optional pagination.

        This method fetches variables from the API and caches them locally.
        If an error happens, value is retrieved from cache.

        Args:
            offset (int, optional): The starting point for fetching variables.
            limit (int, optional): The maximum number of variables to retrieve.

        Returns:
            list[dict]: A list of dictionaries containing variables and their values.
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
