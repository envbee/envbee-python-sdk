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
import time

import platformdirs
import requests
from diskcache import Cache

from .exceptions.envbee_exceptions import RequestError, RequestTimeoutError
from .utils import add_querystring


class Envbee:
    __BASE_URL: str = "https://api.envbee.dev"

    def __init__(
        self, api_key: str, api_secret: bytes | bytearray, base_url: str = None
    ) -> None:
        """Initialize the API client with necessary credentials.

        Args:
            api_key (str): The unique identifier for the API.
            api_secret (bytes | bytearray): The secret key used for authenticating API requests.
            base_url (str, optional): The base URL for the API. Defaults to a predefined URL if not provided.
        """
        self.__base_url = base_url or self.__BASE_URL
        self.__api_key = api_key
        self.__api_secret = api_secret

    def _generate_hmac_header(self, url_path: str) -> str:
        """Generate an HMAC authentication header for the specified URL path.

        This method creates an HMAC header used for API authentication, including the current timestamp
        and a hash of the request content.

        Args:
            url_path (str): The path of the API endpoint to which the request is being made.

        Returns:
            str: The formatted HMAC authorization header.
        """
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
        return auth_header

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
        try:
            content = requests.get(
                url,
                headers={"Authorization": hmac_header, "x-api-key": self.__api_key},
                timeout=timeout,
            )
            if content.status_code == 200:
                return content.json()
            else:
                raise RequestError(
                    content.status_code, f"Failed request: {content.text}"
                )
        except requests.exceptions.Timeout:
            raise RequestTimeoutError(
                f"Request to {url} timed out after {timeout} seconds"
            )

    def _cache_variable(self, variable_name: str, variable_value: str):
        """Cache a variable locally for future retrieval.

        Args:
            variable_name (str): The name of the variable to cache.
            variable_value (str): The value of the variable to cache.
        """
        app_cache_dir = platformdirs.user_cache_dir(
            appname=self.__api_key, appauthor="envbee"
        )
        with Cache(app_cache_dir) as reference:
            reference.set(variable_name, variable_value)

    def _get_variable_from_cache(self, variable_name: str) -> str:
        """Retrieve a variable's value from the local cache.

        Args:
            variable_name (str): The name of the variable to retrieve.

        Returns:
            str: The cached value of the variable, or None if not found.
        """
        app_cache_dir = platformdirs.user_cache_dir(
            appname=self.__api_key, appauthor="envbee"
        )
        with Cache(app_cache_dir) as reference:
            return reference.get(variable_name)

    def _get_variables_from_cache(self) -> list[dict]:
        """Retrieve all cached variables and their values.

        Returns:
            list[dict]: A list of dictionaries containing names and values of cached variables.
        """
        app_cache_dir = platformdirs.user_cache_dir(
            appname=self.__api_key, appauthor="envbee"
        )
        values = []
        with Cache(app_cache_dir) as reference:
            values = [{"name": k, "value": reference[k]} for k in list(reference)]
        return values

    def get_variable(self, variable_name: str) -> str:
        """Retrieve a variable's value by its name.

        This method attempts to fetch the variable from the API, and if it fails, it retrieves
        the value from the local cache.

        Args:
            variable_name (str): The name of the variable to retrieve.

        Returns:
            str: The value of the variable.
        """
        url_path = f"/variables-values/{variable_name}"
        hmac_header = self._generate_hmac_header(url_path)
        final_url = f"{self.__base_url}{url_path}"
        try:
            result = self._send_request(final_url, hmac_header)
            value: str = result.get("value")
            self._cache_variable(variable_name, value)
            return value
        except Exception:
            return self._get_variable_from_cache(variable_name)

    def get_variables(self, offset: int = None, limit: int = None) -> list[dict]:
        """Retrieve a list of variables with optional pagination.

        This method fetches variables from the API and caches them locally.
        If an error happens, value is retrieved from cache.

        Args:
            offset (int, optional): The starting point for fetching variables.
            limit (int, optional): The maximum number of variables to retrieve.

        Returns:
            list[dict]: A list of dictionaries containing variables and their values.
        """
        url_path = "/variables"
        params = {}
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit

        url_path = add_querystring(url_path, params)

        hmac_header = self._generate_hmac_header(url_path)

        final_url = f"{self.__base_url}{url_path}"
        try:
            result = self._send_request(final_url, hmac_header)
            data: dict = result.get("data")
            for v in data:
                self._cache_variable(v["name"], v["value"])
            return data
        except Exception:
            return self._get_variables_from_cache()
